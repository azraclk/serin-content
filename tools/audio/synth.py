"""Serin ambient sound synthesis.

Every sound is generated from scratch with numpy (no samples, no third-party audio), so it is
original work with no license to track. Everything is exactly periodic over LOOP_SECONDS (noise is
shaped in the frequency domain, tones and LFOs sit on whole cycles per loop, one-shot sounds wrap
around the loop point), so the finished file loops with no seam. The app repeats the file for the
session length the listener picked.

Usage:  python -P tools/audio/synth.py velvet --out build
        python -P tools/audio/synth.py all --out build
"""

import argparse
import pathlib

import numpy as np
import soundfile as sf

SR = 44_100
LOOP_SECONDS = 240
N = SR * LOOP_SECONDS
T = np.arange(N) / SR

# Loudness every track is set to, measured with A-weighting (how loud it sounds, not how much
# energy it has), so switching tracks never jumps in volume. Sparse tracks add their own offset.
TARGET_A_DB = -32.5  # the level of the approved first prototype, "velvet"
PEAK_LIMIT_DB = -1.5


def db(x):
    return 20 * np.log10(max(x, 1e-12))


def on_grid(freq):
    """Nearest frequency with a whole number of cycles per loop, so the tone wraps around cleanly."""
    return round(freq * LOOP_SECONDS) / LOOP_SECONDS


def lfo(cycles, phase=0.0):
    """Slow sine with a whole number of cycles per loop (period = LOOP_SECONDS / cycles)."""
    return np.sin(2 * np.pi * cycles * T / LOOP_SECONDS + phase)


# ---------------------------------------------------------------------------------- building blocks

def shaped_noise(rng, amplitude):
    """White noise reshaped by amplitude(f) in the frequency domain; periodic over the loop."""
    spec = rng.normal(size=N // 2 + 1) + 1j * rng.normal(size=N // 2 + 1)
    spec *= amplitude(np.fft.rfftfreq(N, 1 / SR))
    spec[0] = 0
    x = np.fft.irfft(spec, N)
    return x / x.std()


def brown(corner_hz):
    """-6 dB/octave from 60 Hz (brown noise), softened above corner_hz, no sub-bass rumble."""
    def amplitude(f):
        slope = 1.0 / np.maximum(f, 60.0)
        lowpass = 1.0 / np.sqrt(1.0 + (f / corner_hz) ** 4)
        highpass = f**2 / (f**2 + 30.0**2)
        return slope * lowpass * highpass
    return amplitude


def band(lo_hz, hi_hz, tilt):
    """Noise between lo_hz and hi_hz whose level falls with frequency as f^-tilt (0 white, .5 pink, 1 brown)."""
    def amplitude(f):
        fs = np.maximum(f, 1.0)
        high = (fs / lo_hz) ** 2 / np.sqrt(1 + (fs / lo_hz) ** 4)
        low = 1 / np.sqrt(1 + (fs / hi_hz) ** 4)
        return high * low * np.maximum(fs, 100.0) ** -tilt
    return amplitude


def pad(rng, notes, side):
    """Soft sustained chord: each note is a detuned pair with a slow, independent swell."""
    out = np.zeros(N)
    for i, base in enumerate(notes):
        for j, detune in enumerate((-0.18, 0.21)):
            freq = on_grid(base + detune * (1 if side == 0 else -1))
            phase = rng.uniform(0, 2 * np.pi)
            swell = 0.65 + 0.35 * lfo(4 + i * 2 + j, rng.uniform(0, 2 * np.pi))
            tone = np.sin(2 * np.pi * freq * T + phase) + 0.2 * np.sin(2 * np.pi * 2 * freq * T + phase)
            out += swell * tone
    return out / out.std()


def drone(rng, root, side, partials=6):
    """One held note whose overtones slowly come and go, so the timbre keeps breathing."""
    out = np.zeros(N)
    for k in range(1, partials + 1):
        freq = on_grid(root * k + (0.12 if side else -0.12) * k)
        level = lfo(5 + 2 * k, rng.uniform(0, 2 * np.pi)) * 0.35 + 0.65
        out += level / k * np.sin(2 * np.pi * freq * T + rng.uniform(0, 2 * np.pi))
    return out / out.std()


def droplet_layer(rng, rate_per_s, ring_hz, decay_s):
    """Random tiny taps, each ringing briefly at ring_hz (circular convolution keeps it periodic)."""
    count = int(rate_per_s * LOOP_SECONDS)
    taps = np.zeros(N)
    np.add.at(taps, rng.integers(0, N, count), rng.exponential(1.0, count) * rng.choice([-1.0, 1.0], count))
    t = np.arange(int(0.03 * SR)) / SR
    kernel = np.sin(2 * np.pi * ring_hz * t) * np.exp(-t / decay_s)
    x = np.fft.irfft(np.fft.rfft(taps) * np.fft.rfft(kernel, N), N)
    return x / x.std()


def place(buffer, sound, start):
    """Add a one-shot sound at sample `start`, wrapping around the loop point."""
    idx = (start + np.arange(len(sound))) % N
    np.add.at(buffer, idx, sound)


def pan(mono, position):
    """Equal-power pan, position -1 (left) .. 1 (right)."""
    angle = (position + 1) * np.pi / 4
    return np.stack([mono * np.cos(angle), mono * np.sin(angle)], axis=1)


# --------------------------------------------------------------------------------------- the tracks

def velvet(rng):
    """Brown noise whose tone drifts slowly between dark and warm, over a very quiet open chord."""
    channels = []
    common = shaped_noise(rng, brown(1200))
    for side in (0, 1):
        dark = shaped_noise(rng, brown(700))
        warm = shaped_noise(rng, brown(2400))
        mix = 0.5 + 0.28 * lfo(2, 0.4 + side) + 0.22 * lfo(5, 1.7 + side)  # 0..1, 120 s and 48 s drifts
        noise = np.sqrt(1 - mix) * dark + np.sqrt(mix) * warm
        noise = 0.85 * noise + 0.15 * common
        chord = pad(rng, (110.0, 164.81, 220.0, 329.63), side)  # A2 E3 A3 E4: open fifths, no third
        channels.append(noise + 10 ** (-26 / 20) * chord)
    return np.stack(channels, axis=1)


def night_rain(rng):
    """Steady rain on a roof: a soft hiss bed, thousands of tiny drops, distant low rumble."""
    channels = []
    for side in (0, 1):
        hiss = shaped_noise(rng, band(600, 7000, 0.5)) * (1 + 0.12 * lfo(3, side * 1.3))
        drops = sum(droplet_layer(rng, 90, hz, 0.004) for hz in (2300, 3500, 5200))
        rumble = shaped_noise(rng, brown(180))
        channels.append(hiss + 0.28 * drops + 0.3 * rumble)
    return np.stack(channels, axis=1)


def pink_haze(rng):
    """Plain pink noise with a barely noticeable drift in level and stereo balance."""
    common = shaped_noise(rng, band(80, 6000, 0.5))
    channels = []
    for side in (0, 1):
        own = shaped_noise(rng, band(80, 6000, 0.5))
        drift = 1 + 0.10 * lfo(3, 0.7) * (1 if side else -1) + 0.08 * lfo(7, 2.1)
        channels.append((0.75 * own + 0.25 * common) * drift)
    return np.stack(channels, axis=1)


def one_point(rng):
    """A single held D with a slowly shifting colour and a fifth far underneath; nothing to follow."""
    channels = []
    for side in (0, 1):
        note = drone(rng, 146.83, side)  # D3
        fifth = drone(rng, 220.0, side, partials=3)  # A3
        floor = shaped_noise(rng, band(100, 2500, 0.8))
        channels.append(note + 0.35 * fifth + 0.18 * floor)
    return np.stack(channels, axis=1)


def breath_tide(rng):
    """A warm chord that rises and ebbs once every 24 s.

    Deliberately NOT tied to the breathing patterns (8, 19 and 16 s cycles): the sound can never be
    in step with the orb on screen, so a rhythm here would only fight it.
    """
    channels = []
    for side in (0, 1):
        chord = pad(rng, (130.81, 196.0, 261.63, 329.63), side)  # C3 G3 C4 E4
        tide = 0.62 + 0.38 * lfo(10, side * 0.6)
        floor = shaped_noise(rng, brown(900))
        channels.append(tide * chord + 0.5 * floor)
    return np.stack(channels, axis=1)


def shoreline(rng):
    """Waves that build, break into foam and drain, never twice the same; left and right out of step."""
    def swell(phase):
        s = lfo(21, phase) + 0.7 * lfo(26, phase * 1.7 + 1) + 0.5 * lfo(33, phase * 2.3 + 2)
        return ((s - s.min()) / (s.max() - s.min())) ** 2

    channels = []
    for side in (0, 1):
        env = swell(0.3 + side * 0.9)
        body = shaped_noise(rng, band(100, 1600, 0.7))
        foam = shaped_noise(rng, band(1800, 9000, 0.3))
        floor = shaped_noise(rng, band(800, 5000, 0.4))
        channels.append(body * (0.2 + 0.8 * env) + 0.6 * foam * env**1.5 + 0.12 * floor)
    return np.stack(channels, axis=1)


def bell(freq):
    """A small bright chime: three inharmonic partials that die away at different speeds."""
    t = np.arange(int(8 * SR)) / SR
    x = sum(
        level * np.sin(2 * np.pi * freq * ratio * t) * np.exp(-t / tau)
        for ratio, level, tau in ((1.0, 1.0, 1.8), (2.76, 0.35, 1.0), (5.4, 0.15, 0.5))
    )
    return x * np.minimum(1.0, t / 0.003)


def wind_and_chimes(rng):
    """Gusting wind, and now and then a chime from a pentatonic scale (D E F# A B)."""
    wind_channels = []
    for side in (0, 1):
        gust = 0.5 + 0.3 * lfo(3, 0.5 + side) + 0.2 * lfo(7, 2.0 + side)
        dark = shaped_noise(rng, band(60, 500, 0.9))
        bright = shaped_noise(rng, band(250, 2200, 0.5))
        wind_channels.append((np.sqrt(1 - gust) * dark + np.sqrt(gust) * bright) * (0.5 + 0.5 * gust))
    chimes = np.zeros((N, 2))
    scale = (587.33, 659.25, 739.99, 880.0, 987.77, 1174.66)
    when = 0.0
    while when < LOOP_SECONDS:
        chimes += pan_shot(bell(scale[rng.integers(len(scale))]), rng.uniform(-0.8, 0.8), int(when * SR))
        when += rng.uniform(4.0, 14.0)
    return np.stack(wind_channels, axis=1) + 0.55 * chimes


def pan_shot(sound, position, start):
    """Pan a one-shot and wrap it around the loop point as a full-length stereo buffer."""
    out = np.zeros((N, 2))
    stereo = pan(sound, position)
    for ch in (0, 1):
        place(out[:, ch], stereo[:, ch], start)
    return out


def singing_bowl(rng):
    """A struck bowl every ~30 s: beating partials ringing out into near silence."""
    bowl = np.zeros((N, 2))
    pitches = (220.0, 246.94, 277.18, 329.63)  # A3 B3 C#4 E4
    t = np.arange(int(50 * SR)) / SR
    for i in range(8):
        freq = pitches[rng.integers(len(pitches))]
        strike = np.zeros_like(t)
        for ratio, level, tau in ((1.0, 1.0, 9.0), (2.71, 0.45, 5.0), (5.15, 0.18, 2.5)):
            for beat in (0.0, rng.uniform(0.5, 1.4)):  # two close frequencies = the slow wobble of a real bowl
                strike += level * np.sin(2 * np.pi * (freq * ratio + beat) * t + rng.uniform(0, 2 * np.pi)) * np.exp(-t / tau)
        strike *= np.minimum(1.0, t / 0.015)  # soft mallet
        start = int((i * 30 + rng.uniform(-3, 3)) * SR) % N
        bowl += pan_shot(strike, rng.uniform(-0.3, 0.3), start)
    floor = np.stack([shaped_noise(rng, brown(500)) for _ in (0, 1)], axis=1)
    return bowl + 0.06 * floor


# name -> (generator, level offset in dB: sparse sounds sit lower so a strike never startles)
TRACKS = {
    "velvet": (velvet, 0.0),
    "night-rain": (night_rain, 0.0),
    "pink-haze": (pink_haze, 0.0),
    "one-point": (one_point, 0.0),
    "breath-tide": (breath_tide, 0.0),
    "shoreline": (shoreline, 0.0),
    "wind-and-chimes": (wind_and_chimes, -3.0),
    "singing-bowl": (singing_bowl, -8.0),
}


# --------------------------------------------------------------------------------- output and checks

def a_weighted_db(audio):
    """RMS level in dBFS after A-weighting (roughly how loud the ear hears it)."""
    f = np.fft.rfftfreq(len(audio), 1 / SR)
    def ra(freq):
        f2 = freq**2
        return 12194.0**2 * f2**2 / ((f2 + 20.6**2) * np.sqrt((f2 + 107.7**2) * (f2 + 737.9**2)) * (f2 + 12194.0**2))
    weight = ra(f) / ra(np.array([1000.0]))[0]
    weighted = np.fft.irfft(np.fft.rfft(audio, axis=0) * weight[:, None], len(audio), axis=0)
    return db(np.sqrt(np.mean(weighted**2)))


def normalize(audio, offset_db):
    audio = audio - audio.mean(axis=0)
    audio *= 10 ** ((TARGET_A_DB + offset_db - a_weighted_db(audio)) / 20)
    peak = np.abs(audio).max()
    if db(peak) > PEAK_LIMIT_DB:
        print(f"  peak {db(peak):.1f} dBFS over limit, turning down")
        audio *= 10 ** (PEAK_LIMIT_DB / 20) / peak
    return audio


def seam_ratio(audio):
    """Step across the loop point relative to the largest normal step (99.9th percentile) in the same
    channel; at or below 1 the seam is no bigger than the signal's own movement, so no click."""
    jump = np.abs(audio[0] - audio[-1])
    biggest = np.percentile(np.abs(np.diff(audio, axis=0)), 99.9, axis=0)
    return (jump / biggest).max()


def render(name, out_dir, seed):
    generate, offset_db = TRACKS[name]
    audio = normalize(generate(np.random.default_rng(seed)), offset_db)
    path = out_dir / f"{name}.ogg"
    # One huge write overflows the stack inside libsndfile's Vorbis encoder, so write in 1 s blocks.
    with sf.SoundFile(path, "w", SR, audio.shape[1], format="OGG", subtype="VORBIS") as out:
        for start in range(0, len(audio), SR):
            out.write(audio[start:start + SR].astype(np.float32))

    decoded, _ = sf.read(path)
    kbps = path.stat().st_size * 8 / LOOP_SECONDS / 1000
    print(f"{path}: {path.stat().st_size / 1e6:.1f} MB, {kbps:.0f} kbps, {len(decoded) / SR:.0f} s")
    print(f"  loudness {a_weighted_db(decoded):.1f} dBFS(A), peak {db(np.abs(decoded).max()):.1f} dBFS, "
          f"loop seam {seam_ratio(decoded):.2f} (<= 1 is clean)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("track", choices=[*TRACKS, "all"])
    parser.add_argument("--out", type=pathlib.Path, default=pathlib.Path("build"))
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    for name in TRACKS if args.track == "all" else [args.track]:
        render(name, args.out, args.seed)


if __name__ == "__main__":
    main()
