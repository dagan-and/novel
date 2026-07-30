from pathlib import Path
import tempfile
import unittest

import convert_html


class ConvertHtmlTests(unittest.TestCase):
    def test_render_episode_converts_title_dialogue_message_and_image(self):
        markdown = """# ep.001 테스트

비가 왔다.

[알림] 장소가 변경되었습니다.

[주인공] "우산 있어요?"

![비 오는 카페 앞](../../images/ep001/scene-01.png)
"""

        rendered = convert_html.render_episode(markdown, 1)

        self.assertIn("<h1>ep.001 테스트</h1>", rendered)
        self.assertIn('<p class="message"><span class="message-sender">[알림]</span>', rendered)
        self.assertIn('<p class="dialogue">', rendered)
        self.assertIn('<img src="../../images/ep001/scene-01.png" alt="비 오는 카페 앞" loading="lazy">', rendered)
        self.assertIn("<title>wish-real ep.001</title>", rendered)

    def test_convert_episode_writes_html_without_publishing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            episodes = root / "episodes"
            html_dir = root / "html"
            source_dir = episodes / "001-100"
            source_dir.mkdir(parents=True)
            (source_dir / "ep.001.md").write_text(
                "# ep.001\n\n본문.\n\n![삽화](../../images/ep001/scene-01.png)\n",
                encoding="utf-8",
            )

            old_root = convert_html.ROOT
            old_episodes = convert_html.EPISODES_DIR
            old_html = convert_html.HTML_DIR
            try:
                convert_html.ROOT = root
                convert_html.EPISODES_DIR = episodes
                convert_html.HTML_DIR = html_dir

                output = convert_html.convert_episode(1)
            finally:
                convert_html.ROOT = old_root
                convert_html.EPISODES_DIR = old_episodes
                convert_html.HTML_DIR = old_html

            self.assertEqual(html_dir / "001-100" / "ep.001.html", output)
            written = output.read_text(encoding="utf-8")
            self.assertIn('<img src="../../images/ep001/scene-01.png" alt="삽화" loading="lazy">', written)


if __name__ == "__main__":
    unittest.main()
