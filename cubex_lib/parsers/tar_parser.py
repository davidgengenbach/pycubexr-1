import tarfile
from typing import List
from xml.etree import ElementTree

from cubex_lib.classes import Metric, MetricValues, CNode
from cubex_lib.parsers.anchor_xml_parser import CubexAnchorXMLParser
from cubex_lib.parsers.metrics_parser import CubexMetricsParser
from cubex_lib.utils import chunk_list


class CubexTarParser(object):
    metrics_parser: CubexMetricsParser
    anchor_parser: CubexAnchorXMLParser

    def __init__(self, cubex_filename: str):
        self.cubex_filename = cubex_filename
        self.cubex_file = tarfile.open(self.cubex_filename, 'r')

        with self.cubex_file.extractfile('anchor.xml') as anchor_file:
            anchor = ElementTree.parse(anchor_file)
            self.anchor_parser = CubexAnchorXMLParser(anchor)
        self.metrics_parser = CubexMetricsParser(self.anchor_parser)

    def get_metric_values(
            self,
            metric: Metric
    ) -> MetricValues:
        index_file_name = f'{metric.id}.index'
        data_file_name = f'{metric.id}.data'

        if index_file_name not in [x.name for x in self.cubex_file.getmembers()]:
            # TODO: this should be a custom Exception so that it can be catched more easily
            raise Exception(f'The cubex file does NOT contain values for the metric ({metric})')

        with self.cubex_file.extractfile(index_file_name) as index_file, self.cubex_file.extractfile(
                data_file_name) as data_file:
            metric_values = self.metrics_parser.get_metric_values(
                metric=metric,
                index_file=index_file,
                data_file=data_file
            )

            num_locations = len(self.anchor_parser.get_locations())
            cnodes: List[CNode] = [
                self.anchor_parser.get_cnode(cnode_index) for cnode_index in metric_values.cnode_indices
            ]

            assert len(metric_values.values) == len(cnodes) * num_locations

            values = chunk_list(metric_values.values, num_locations)

            assert len(values) == len(cnodes)
            assert all(len(values_) == num_locations for values_ in values)

            return metric_values
