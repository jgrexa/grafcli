"""Local resources.

TODO: simplify and refactor private methods.

"""
import os
import json

from grafcli.exceptions import InvalidPath, InvalidDocument, DocumentNotFound
from grafcli.config import config
from grafcli.documents import Dashboard, Row, Panel

DASHBOARDS = 'dashboards'
ROWS = 'rows'
PANELS = 'panels'

LOCAL_RESOURCES = (DASHBOARDS, ROWS, PANELS)

DATA_DIR = os.path.expanduser(config['resources'].get('data-dir', ''))
DASHBOARDS_DIR = os.path.join(DATA_DIR, DASHBOARDS)
ROWS_DIR = os.path.join(DATA_DIR, ROWS)
PANELS_DIR = os.path.join(DATA_DIR, PANELS)

DIR_DOCUMENTS = {
    DASHBOARDS: Dashboard,
    ROWS: Row,
    PANELS: Panel,
}


class LocalResources(object):

    def __init__(self):
        make_local_dirs()

    def list(self, parts):
        directory = parts.pop(0)

        if directory not in LOCAL_RESOURCES:
            raise InvalidPath("Invalid local directory: {}".format(directory))

        if not parts:
            return list_files(os.path.join(DATA_DIR, directory))

        if directory == DASHBOARDS:
            return self._list_dashboards(parts)
        elif directory == ROWS:
            return self._list_rows(parts)
        elif directory == PANELS:
            return self._list_panels(parts)

    def _list_dashboards(self, parts):
        dashboard_name = parts.pop(0) if parts else None
        row_name = parts.pop(0) if parts else None
        panel_name = parts.pop(0) if parts else None

        source = read_file(DASHBOARDS_DIR, dashboard_name)
        dashboard = Dashboard(source, dashboard_name)

        if not row_name:
            return [row.name for row in dashboard.rows]

        panels = [panel.name for panel in dashboard.row(row_name).panels]

        if panel_name:
            if panel_name in panels:
                raise InvalidPath("Panel contains no sub-nodes")
            else:
                raise InvalidPath("There is no such panel: {}".format(panel_name))
        else:
            return panels

    def _list_rows(self, parts):
        row_name = parts.pop(0) if parts else None
        if parts:
            raise InvalidPath("Panels contain no sub-nodes")

        source = read_file(ROWS_DIR, row_name)
        row = Row(source)

        return [panel.name for panel in row.panels]

    def _list_panels(self, parts):
        raise InvalidPath("Panels contain no sub-nodes")

    def get(self, parts):
        directory = parts.pop(0)

        if directory not in LOCAL_RESOURCES:
            raise InvalidPath("Invalid local directory: {}".format(directory))

        if directory == DASHBOARDS:
            return self._get_dashboards(parts)
        elif directory == ROWS:
            return self._get_rows(parts)
        elif directory == PANELS:
            return self._get_panels(parts)

    def _get_dashboards(self, parts):
        dashboard_name = parts.pop(0) if parts else None
        row_name = parts.pop(0) if parts else None
        panel_name = parts.pop(0) if parts else None
        if parts:
            raise InvalidPath("Panels contain no sub-nodes")

        source = read_file(DASHBOARDS_DIR, dashboard_name)
        dashboard = Dashboard(source, dashboard_name)

        if row_name:
            row = dashboard.row(row_name)

            if panel_name:
                return row.panel(panel_name)
            else:
                return row

        return dashboard

    def _get_rows(self, parts):
        row_name = parts.pop(0) if parts else None
        panel_name = parts.pop(0) if parts else None
        if parts:
            raise InvalidPath("Panels contain no sub-nodes")

        source = read_file(ROWS_DIR, row_name)
        row = Row(source)

        if panel_name:
            return row.panel(panel_name)
        else:
            return row

    def _get_panels(self, parts):
        panel_name = parts.pop(0) if parts else None
        if parts:
            raise InvalidPath("Panels contain no sub-nodes")

        source = read_file(PANELS_DIR, panel_name)
        return Panel(source)

    def save(self, parts, document):
        directory = parts[0]

        try:
            origin_document = self.get(list(parts))
            origin_document.update(document)

            top_parent = origin_document
            while top_parent.parent:
                top_parent = top_parent.parent

            document = top_parent
        except DocumentNotFound:
            document_class = DIR_DOCUMENTS[directory]
            if not isinstance(document, document_class):
                raise InvalidDocument("Can not add {} to {}"
                                      .format(type(document).__name__, directory))

        if len(parts) >= 2:
            file_name = parts[-1]
        else:
            file_name = document.name

        write_file(os.path.join(DATA_DIR, directory), file_name, document.source)


def to_file_format(filename):
    return "{}.json".format(filename)


def from_file_format(filename):
    return filename.replace('.json', '')


def list_files(path):
    full_path = os.path.join(path)
    if os.path.isdir(full_path):
        return [from_file_format(file)
                for file in os.listdir(full_path)]
    else:
        raise InvalidPath("No sub-nodes found")


def read_file(directory, name):
    file = to_file_format(name)
    full_path = os.path.join(directory, file)

    if not name or not os.path.isfile(full_path):
        raise DocumentNotFound("File not found: {}".format(full_path))

    with open(full_path, 'r') as f:
        return json.loads(f.read())


def write_file(directory, name, data):
    file = to_file_format(name)
    full_path = os.path.join(directory, file)

    with open(full_path, 'w') as f:
        f.write(json.dumps(data))


def make_local_dirs():
    if DATA_DIR:
        for path in (DATA_DIR, DASHBOARDS_DIR, ROWS_DIR, PANELS_DIR):
            os.makedirs(path, mode=0o755, exist_ok=True)
