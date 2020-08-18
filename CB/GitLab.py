import io
import shutil
import zipfile
import requests
from . import retry, HEADERS


class GitLabAddon:
    @retry()
    def __init__(self, projectid, branch):
        self.project = requests.get(f'https://git.tukui.org/api/v4/projects/{projectid}', headers=HEADERS)
        if self.project.status_code == 404:
            raise RuntimeError(projectid)
        else:
            self.project = self.project.json()
        self.branch = requests.get(f'https://git.tukui.org/api/v4/projects/{projectid}/repository/branches/{branch}',
                                   headers=HEADERS)
        if self.branch.status_code == 404:
            raise RuntimeError(projectid)
        else:
            self.branch = self.branch.json()
        self.name = self.project['name']
        self.pathWithNamespace = self.project['path_with_namespace']
        self.shortPath = self.pathWithNamespace.split('/')[1]
        self.downloadUrl = f'https://git.tukui.org/{self.pathWithNamespace}/-/archive/{branch}/{self.shortPath}-{branch}.zip'
        self.currentVersion = self.branch['commit']['short_id']
        self.branch = branch
        self.archive = None
        self.directories = []

    @retry()
    def get_addon(self):
        self.archive = zipfile.ZipFile(io.BytesIO(requests.get(self.downloadUrl, headers=HEADERS).content))
        for file in self.archive.namelist():
            file_info = self.archive.getinfo(file)
            if file_info.is_dir() and file_info.filename.count('/') == 2 and '.gitlab' not in file_info.filename:
                print(file_info.filename.split('/')[1])
                self.directories.append(file_info.filename.split('/')[1])
        self.directories = list(filter(None, set(self.directories)))
        if len(self.directories) == 0:
            raise RuntimeError(f'{self.name}.\nProject package is corrupted or incorrectly packaged.')

    def install(self, path):
        print(path)

        self.archive.extractall(path)
        for directory in self.directories:
            print(directory)
            shutil.rmtree(path / directory, ignore_errors=True)
            # FIXME - Python bug #32689
            shutil.move(str(path / f'{self.shortPath}-{self.branch}' / directory), str(path))
        shutil.rmtree(path / f'{self.shortPath}-{self.branch}')
