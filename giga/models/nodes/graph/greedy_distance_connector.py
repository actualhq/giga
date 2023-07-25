import math
from typing import List
from queue import PriorityQueue
import numpy as np

from giga.schemas.geo import UniqueCoordinate, PairwiseDistance
from giga.models.nodes.graph.pairwise_distance_model import PairwiseDistanceModel
from giga.utils.progress_bar import managed_progress_bar
from giga.schemas.distance_cache import GreedyConnectCache


EPS = 1e-4  # for tie-breakers in queue with equal distances


# helpers below can be pulled into a distance queue class in a future refactor
def add_distances(q, distances):
    for d in distances:
        priority, item = d.distance + np.random.uniform(0.0, EPS), d
        q.put((priority, item))
    return q


def move_item(source, target, identifier):
    item = source.pop(identifier)
    target[identifier] = item
    return item


class GreedyDistanceConnector:

    """
    Uses a greedy approach to iteratively connect the closest unconnected nodes to
    a subset of connected nodes.
    When configured with the dynamic_connect parameter to True
    this runs Prim's algorithm: https://en.wikipedia.org/wiki/Prim%27s_algorithm
    """

    def __init__(
        self,
        connected: List[UniqueCoordinate],
        distance_cache: GreedyConnectCache = None,
        **kwargs
    ):
        self.connected = connected
        # used to compute distances between coordinate pairs
        self.distance_model = kwargs.get("distance_model", PairwiseDistanceModel())
        # if configured, allows connections that are less than the configured length
        self.maximum_connection_length_m = kwargs.get(
            "maximum_connection_length_m", math.inf
        )
        # if set to False only allows connections between the existing connected set
        # when set True, new dynamic connected coordinates can be used as connections
        self.dynamic_connect = kwargs.get("dynamic_connect", True)
        self.progress_bar = kwargs.get("progress_bar", False)
        self._cache = (
            distance_cache if distance_cache is not None else GreedyConnectCache()
        )

    def _queue_non_cached(self, q, set1, set2):
        distances = self.distance_model.run((set1, set2))
        distances = list(
            filter(
                lambda x: x is not None
                and x.distance < self.maximum_connection_length_m,
                distances,
            )
        )
        return add_distances(q, distances)

    def _queue_from_cache(self, q, set1, set2, cache):
        coord_ids1 = set([c.coordinate_id for c in set1])
        coord_ids2 = set([c.coordinate_id for c in set2])
        if cache.cache_type == "one-to-one":
            distances = [cache.lookup.get(cid, None) for cid in coord_ids1]
        elif cache.cache_type == "one-to-many":
            # single cache in set 2
            distances = []
            for cid in coord_ids2:
                distances += cache.lookup.get(cid, [None])
        else:
            raise Exception("Trying to use a cache of unsupported type")
        distances = list(
            filter(
                lambda x: x is not None
                and x.distance < self.maximum_connection_length_m
                and (
                    x.coordinate1.coordinate_id in coord_ids1
                    or x.coordinate1.coordinate_id in coord_ids2
                )
                and (
                    (
                        x.coordinate2.coordinate_id in coord_ids1
                        or x.coordinate2.coordinate_id in coord_ids2
                    )
                ),  # add check here to make sure coordinates in distance are in both sets
                distances,
            )
        )
        return add_distances(q, distances)

    def queue_pairwise_distances(self, q, set1, set2, cache=None):
        if cache:
            return self._queue_from_cache(q, set1, set2, cache)
        else:
            return self._queue_non_cached(q, set1, set2)

    def run(self, data: List[UniqueCoordinate], **kwargs) -> List[PairwiseDistance]:
        """
        Connects a list of unconnected unique coordinates in the input to
        a set of connected unique coordinates until no more connections are possible

        param: data, a List[UniqueCoordinate] representing a collection of
               UniqueCoordinates that contain a unique identifier and a location (usually lat/lon)
        :return list of PairwiseDistance objects which represent an ordered an connected coordinate pairs
                added to the set of connected coordinates in this model.
        """
        greedy_connected = []
        queue = (
            PriorityQueue()
        )  # priority queue is used to connect closest unconnected coordinates
        # create two look ups for connected (self.connected)
        # and unconnected (input data) coordinate sets
        connected_coordinates = {x.coordinate_id: x for x in self.connected}
        unconnected_coordinates = {x.coordinate_id: x for x in data}
        # create a source tracker
        sources = {x.coordinate_id: x.coordinate_id for x in self.connected}
        # add pairwise distances between all coordinates and in data to priority queue
        queue = self.queue_pairwise_distances(
            queue, data, self.connected, cache=self._cache.connected_cache
        )
        if self.progress_bar:
            pbar = managed_progress_bar(len(data), description="Distance Connect Model")
        while not queue.empty():
            # iterate until priority queue is empty
            d, candidate = queue.get()  # fetch coordinate pair with closest distance
            id1, id2 = candidate.pair_ids
            connected1, connected2 = (
                id1 in connected_coordinates,
                id2 in connected_coordinates,
            )
            if connected1 and connected2:
                # if both items are connected skip, used to handle identical coordinates
                # not needed if coordinates in connected and unconnected sets are unique
                continue
            elif connected2:
                # coordinate 1 is not connected
                # make new connection move from unconnected lookup to connected lookup
                new_connection = move_item(
                    unconnected_coordinates, connected_coordinates, id1
                )
                # fetch for source use id2 if doesn't exist
                candidate.coordinate1.properties["source"] = sources[id2]
                sources[id1] = sources[id2]
                greedy_connected.append(candidate)
                if self.progress_bar:
                    pbar.update(1)
                if self.dynamic_connect:
                    # if other unconnected coordinates can connect to new connection
                    queue = self.queue_pairwise_distances(
                        queue,
                        list(unconnected_coordinates.values()),
                        [new_connection],
                        cache=self._cache.unconnected_cache,
                    )
            else:
                # neither items are connected, skip
                continue
        if self.progress_bar:
            pbar.update(pbar.total - pbar.n)
            pbar.close()
        return greedy_connected
