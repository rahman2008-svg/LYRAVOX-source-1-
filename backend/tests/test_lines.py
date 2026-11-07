"""Logic tests on SYNTHETIC segments (hand-written inputs, not model output)."""
import unittest
from helpers import *
from lyravox_ai import lines as L
from lyravox_ai.engines import RawSegment, Word


def W(start, end, text, p=0.9): return Word(start, end, text, p)


class LinesTests(unittest.TestCase):
    def test_confidence_range_and_none(self):
        s = RawSegment(0, 1, 'x', avg_logprob=-0.1, no_speech_prob=0.0)
        self.assertGreater(L.segment_confidence(s), 0.85)
        self.assertLess(L.segment_confidence(RawSegment(0, 1, 'x', avg_logprob=-1.5, no_speech_prob=0.5)), 0.2)
        self.assertIsNone(L.segment_confidence(RawSegment(0, 1, 'x')))

    def test_hallucination_filter(self):
        self.assertTrue(L.is_hallucination(RawSegment(0, 1, '   ')))
        self.assertTrue(L.is_hallucination(RawSegment(0, 1, '...')))
        self.assertTrue(L.is_hallucination(RawSegment(0, 5, 'la la la', -0.9, 0.9, 1.0)))
        self.assertTrue(L.is_hallucination(RawSegment(0, 5, 'la la la la la', -0.3, 0.1, 3.5)))
        self.assertFalse(L.is_hallucination(RawSegment(0, 5, 'আমার সোনার বাংলা', -0.3, 0.1, 1.2)))

    def test_repeat_loop_is_cut(self):
        segs = [RawSegment(i, i + 1, 'Thanks for watching', -0.3, 0.1, 1.0) for i in range(6)] + [RawSegment(7, 8, 'real line', -0.3, 0.1, 1.0)]
        out = L.drop_repeats(segs)
        self.assertEqual([s.text for s in out], ['Thanks for watching'] * 2 + ['real line'])

    def test_split_at_word_pause_keeps_exact_times(self):
        seg = RawSegment(0, 6, 'one two three four', -0.2, 0.0, 1.0, [W(0, .5, ' one'), W(.5, 1, ' two'), W(3, 3.5, ' three'), W(3.5, 4, ' four')])
        out = L.build_lines([seg])
        self.assertEqual([l['text'] for l in out], ['one two', 'three four'])
        self.assertEqual((out[0]['start'], out[0]['end'], out[1]['start'], out[1]['end']), (0, 1, 3, 4))
        self.assertFalse(out[0]['approx']); self.assertEqual(len(out[0]['words']), 2)

    def test_long_line_split_by_length(self):
        ws = [W(i * .4, i * .4 + .35, ' word%02d' % i) for i in range(20)]
        seg = RawSegment(0, 8, ''.join(w.text for w in ws).strip(), -0.2, 0.0, 1.0, ws)
        out = L.build_lines([seg], max_chars=30)
        self.assertGreater(len(out), 2)
        for l in out: self.assertLessEqual(len(l['text']), 36)

    def test_no_words_interpolates_and_flags_approx(self):
        seg = RawSegment(10, 20, 'aaaa bbbb cccc dddd eeee ffff gggg hhhh', -0.2, 0.0, 1.0)
        out = L.build_lines([seg], max_chars=20)
        self.assertGreater(len(out), 1)
        self.assertTrue(all(l['approx'] for l in out))
        self.assertAlmostEqual(out[0]['start'], 10, places=1); self.assertAlmostEqual(out[-1]['end'], 20, places=1)
        for a, b in zip(out, out[1:]): self.assertLessEqual(a['end'], b['start'] + 0.011)

    def test_bangla_conjuncts_never_cut(self):
        text = 'ক্ষণিকের স্বপ্ন স্ট্রিট দৃষ্টি ' * 4
        a, b = L.split_text_at(text.strip(), 17)
        self.assertEqual((a + ' ' + b).replace('  ', ' '), text.strip())
        for part in (a, b):
            self.assertFalse(part.startswith(('্', 'া', 'ি')), part)
            self.assertFalse(part.endswith('্'), part)
        # a cut index right after a hasanta / before a vowel sign is refused
        self.assertFalse(L._is_safe_cut('ক্ষ', 2)); self.assertFalse(L._is_safe_cut('কি', 1))

    def test_bangla_text_survives_build_lines(self):
        seg = RawSegment(0, 4, 'আমার সোনার বাংলা আমি তোমায় ভালোবাসি', -0.2, 0.0, 1.0)
        out = L.build_lines([seg], max_chars=20)
        self.assertEqual(' '.join(l['text'] for l in out), seg.text)

    def test_overlaps_are_removed_and_ids_sequential(self):
        out = L.build_lines([RawSegment(0, 5, 'first', -0.2, 0, 1), RawSegment(3, 6, 'second', -0.2, 0, 1)])
        self.assertLessEqual(out[0]['end'], out[1]['start']); self.assertEqual([l['id'] for l in out], [1, 2])

    def test_instrumentals(self):
        ls = [{'start': 8, 'end': 10}, {'start': 11, 'end': 12}, {'start': 30, 'end': 31}]
        self.assertEqual(L.find_instrumentals(ls, 45, 6), [{'start': 0.0, 'end': 8}, {'start': 12, 'end': 30}, {'start': 31, 'end': 45}])
        self.assertEqual(L.find_instrumentals(ls, 33, 6), [{'start': 0.0, 'end': 8}, {'start': 12, 'end': 30}])

    def test_editor_syntax_escaping_and_format(self):
        self.assertEqual(L.sanitize_for_editor('a/b | c *d* !'), 'a b c d')
        self.assertEqual(L.sanitize_for_editor('# [x] hi!!'), 'x] hi')
        self.assertEqual(L.fmt_ts(75.5), '[01:15.50]'); self.assertEqual(L.fmt_ts(0), '[00:00.00]')
        txt = L.to_editor_lyrics([{'start': 12.0, 'text': 'line one'}, {'start': 20.25, 'text': 'আমার/সোনার'}], [{'start': 0, 'end': 12}])
        self.assertEqual(txt.split('\n'), ['[00:00.00][interlude 12]', '[00:12.00]line one', '[00:20.25]আমার সোনার'])
        self.assertEqual(L.to_editor_lyrics([], [{'start': 0, 'end': 6.5}]), '[00:00.00][interlude 7]')       # half-up rounding, same as the browser
        self.assertEqual(L.to_editor_lyrics([{'start': 1, 'text': 'x'}], timestamps=False), 'x')


if __name__ == '__main__':
    unittest.main()
