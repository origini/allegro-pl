import allegro_pl
import toml


def test_version():
    def get_project_version(self):
        return toml.load('pyproject.toml')['tool']['poetry']['version']

    def test_version_matches(self):
        self.assertEqual(self.get_project_version(), allegro_pl.__version__)
