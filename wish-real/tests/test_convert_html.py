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

    def test_main_generates_character_index_and_profile_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            episodes = root / "episodes"
            html_dir = root / "html"
            characters = root / "characters"
            assets = root / "character_assets"
            source_dir = episodes / "001-100"
            source_dir.mkdir(parents=True)
            characters.mkdir()
            (source_dir / "ep.001.md").write_text("# ep.001\n\n본문.\n", encoding="utf-8")
            (characters / "김초연.md").write_text(
                "# 김초연\n\n## 기본 정보\n\n- 이름: 김초연\n- 핵심 역할: 첫 공식 여자친구.\n\n### 외형\n\n맑은 인상.\n",
                encoding="utf-8",
            )
            (characters / "캐릭터양식.md").write_text("# 양식\n", encoding="utf-8")
            image_dir = assets / "김초연" / "references"
            image_dir.mkdir(parents=True)
            (image_dir / "main.png").write_bytes(b"fake image")

            old_root = convert_html.ROOT
            old_episodes = convert_html.EPISODES_DIR
            old_html = convert_html.HTML_DIR
            old_characters = getattr(convert_html, "CHARACTERS_DIR", None)
            old_assets = getattr(convert_html, "CHARACTER_ASSETS_DIR", None)
            try:
                convert_html.ROOT = root
                convert_html.EPISODES_DIR = episodes
                convert_html.HTML_DIR = html_dir
                convert_html.CHARACTERS_DIR = characters
                convert_html.CHARACTER_ASSETS_DIR = assets

                exit_code = convert_html.main([])
            finally:
                convert_html.ROOT = old_root
                convert_html.EPISODES_DIR = old_episodes
                convert_html.HTML_DIR = old_html
                if old_characters is None:
                    delattr(convert_html, "CHARACTERS_DIR")
                else:
                    convert_html.CHARACTERS_DIR = old_characters
                if old_assets is None:
                    delattr(convert_html, "CHARACTER_ASSETS_DIR")
                else:
                    convert_html.CHARACTER_ASSETS_DIR = old_assets

            self.assertEqual(0, exit_code)
            self.assertTrue((html_dir / "index.html").exists())
            self.assertTrue((html_dir / "characters.html").exists())
            self.assertTrue((html_dir / "characters" / "김초연.html").exists())
            site_index = (html_dir / "index.html").read_text(encoding="utf-8")
            index = (html_dir / "characters.html").read_text(encoding="utf-8")
            profile = (html_dir / "characters" / "김초연.html").read_text(encoding="utf-8")
            self.assertIn('href="001-100/ep.001.html"', site_index)
            self.assertIn('href="characters.html"', site_index)
            self.assertIn('href="characters/김초연.html"', index)
            self.assertIn('<img src="../character_assets/김초연/references/main.png" alt="김초연" loading="lazy">', index)
            self.assertNotIn("캐릭터양식", index)
            self.assertIn("<title>김초연</title>", profile)
            self.assertIn('<img src="../../character_assets/김초연/references/main.png" alt="김초연"', profile)
            self.assertIn("<h2>기본 정보</h2>", profile)


if __name__ == "__main__":
    unittest.main()
