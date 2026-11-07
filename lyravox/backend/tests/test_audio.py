"""REAL tests: ffmpeg / ffprobe against generated audio files in every supported container."""
import os, shutil, unittest
from helpers import *
from lyravox_ai import audio
from lyravox_ai.errors import AudioError


class AudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = tmpdir()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.d, ignore_errors=True)

    def test_probe_and_decode_every_supported_format(self):
        for fmt in ('wav', 'mp3', 'ogg', 'm4a', 'aac'):
            with self.subTest(fmt=fmt):
                if not encoder_available(fmt):
                    self.skipTest(f'ffmpeg here has no {fmt} encoder')
                p = make_audio(os.path.join(self.d, 'a.' + fmt), 6.0, 2.0, 1.0)
                info = audio.probe(p)
                self.assertAlmostEqual(info['duration'], 6.0, delta=0.4)
                out = os.path.join(self.d, f'dec_{fmt}.wav')
                audio.decode(p, out)
                i2 = audio.probe(out)
                self.assertEqual((i2['sample_rate'], i2['channels']), (16000, 1))
                self.assertAlmostEqual(i2['duration'], info['duration'], delta=0.4)

    def test_probe_rejects_non_audio(self):
        p = os.path.join(self.d, 'fake.mp3')
        open(p, 'wb').write(b'this is not audio at all' * 100)
        with self.assertRaises(AudioError):
            audio.probe(p)

    def test_probe_rejects_truncated_garbage_header(self):
        p = os.path.join(self.d, 'trunc.wav')
        open(p, 'wb').write(b'RIFF\x00\x00\x00\x00WAVEfmt ')
        with self.assertRaises(AudioError):
            audio.probe(p)

    def test_silence_detection_positions(self):
        p = make_audio(os.path.join(self.d, 's.wav'), 10.0, 3.0, 2.0)       # sound 0-3, silence 3-5, sound 5-8, silence 8-10
        sil = audio.close_silences(audio.detect_silences(p, -35, 0.6), 10.0)
        self.assertEqual(len(sil), 2, sil)
        self.assertAlmostEqual(sil[0][0], 3.0, delta=0.15); self.assertAlmostEqual(sil[0][1], 5.0, delta=0.15)
        self.assertAlmostEqual(sil[1][0], 8.0, delta=0.15); self.assertAlmostEqual(sil[1][1], 10.0, delta=0.2)

    def test_first_sound(self):
        self.assertEqual(audio.first_sound([], 10), 0.0)
        self.assertEqual(audio.first_sound([(0.0, 4.2)], 10), 4.2)
        self.assertEqual(audio.first_sound([(3.0, 4.0)], 10), 0.0)

    def test_clip_decode_duration(self):
        p = make_audio(os.path.join(self.d, 'c.wav'), 10.0, 3.0, 2.0)
        out = os.path.join(self.d, 'clip.wav')
        audio.decode(p, out, 2.0, 7.0)
        self.assertAlmostEqual(audio.probe(out)['duration'], 5.0, delta=0.1)

    def test_plan_chunks_cuts_in_silence(self):
        # 20 min with a silence around every 100 s; target chunk 300 s -> cuts must land inside silences near 300/600/900/1200
        sil = [(k * 100 - 1.0, k * 100 + 1.0) for k in range(1, 12)]
        ch = audio.plan_chunks(1230.0, sil, 300)
        self.assertGreaterEqual(len(ch), 4)
        self.assertEqual(ch[0][0], 0.0); self.assertEqual(ch[-1][1], 1230.0)
        for (a, b), (c, d) in zip(ch, ch[1:]):
            self.assertEqual(b, c)                                              # contiguous, no gaps / overlaps
        for a, b in ch[:-1]:
            self.assertTrue(any(s <= b <= e for s, e in sil), f'cut {b} is not inside a silence')
        for a, b in ch:
            self.assertLessEqual(b - a, 300 * 1.45)

    def test_plan_chunks_without_silence_cuts_at_target(self):
        ch = audio.plan_chunks(1000.0, [], 300)
        self.assertEqual(ch[0], (0.0, 300.0)); self.assertAlmostEqual(ch[-1][1], 1000.0)

    def test_short_audio_single_chunk(self):
        self.assertEqual(audio.plan_chunks(200.0, [], 300), [(0.0, 200.0)])


if __name__ == '__main__':
    unittest.main()
