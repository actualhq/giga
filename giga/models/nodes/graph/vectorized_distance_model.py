from typing import List, Tuple
from pydantic import validate_arguments
from sklearn.metrics.pairwise import haversine_distances
from math import radians
import math
import numpy as np

from giga.schemas.geo import UniqueCoordinate, PairwiseDistance
from giga.utils.progress_bar import progress_bar as pb


RADIUS_EARTH_M = 6371000.0
DEFAULT_N_CHUNKS = 100


class VectorizedDistanceModel:
    """
    This model uses sklearn's haversine_distances function to compute pairwise distances
    between two sets of coordinates. It is significantly more performant than the PairwiseDistanceModel
    but requires that the coordinates be converted to radians first.
    """

    def __init__(self, **kwargs):
        self.progress_bar = kwargs.get("progress_bar", False)
        self.n_nearest_neighbors = kwargs.get("n_nearest_neighbors", math.inf)

    def _to_radian_vector(self, coordinates: List[UniqueCoordinate]):
        # convert to an (n x 2) array of radians
        return np.array(
            [[radians(c.coordinate[0]), radians(c.coordinate[1])] for c in coordinates]
        )

    def _get_closest(self, ordered_distances, coordinates):
        # return the n nearest neighbors and their distances
        if self.n_nearest_neighbors >= len(coordinates):
            return coordinates, ordered_distances
        idxs = np.argsort(ordered_distances)[: self.n_nearest_neighbors]
        return np.array(coordinates)[idxs], ordered_distances[idxs]

    @validate_arguments
    def run(
        self, data: Tuple[List[UniqueCoordinate], List[UniqueCoordinate]], **kwargs
    ) -> List[PairwiseDistance]:
        """
        This method computes pairwise distances between two sets of coordinates
        using sklearn's haversine_distances function. It returns a list of PairwiseDistance objects.

        Inputs
        ----------
        data : Tuple[List[UniqueCoordinate]], List[UniqueCoordinate]]
            A tuple of two lists of UniqueCoordinate objects

        Returns
        ----------
        pairs: List[PairwiseDistance]
            A list of PairwiseDistance objects
        """
        progress_bar = kwargs.get("progress_bar", self.progress_bar)
        set1, set2 = data
        # convert to vectors
        vecs1, vecs2 = self._to_radian_vector(set1), self._to_radian_vector(set2)
        distances = haversine_distances(vecs1, vecs2) * RADIUS_EARTH_M
        # return distances
        pairs = []
        iterable = pb(set1) if progress_bar else set1
        for i, c1 in enumerate(iterable):
            closest_coords, closest_dist = self._get_closest(distances[i], set2)
            for j, c2 in enumerate(closest_coords):
                pairs.append(
                    PairwiseDistance(
                        pair_ids=(c1.coordinate_id, c2.coordinate_id),
                        coordinate1=c1,
                        coordinate2=c2,
                        distance=closest_dist[j],
                    )
                )
        return pairs

    @validate_arguments
    def run_chunks(
        self, data: Tuple[List[UniqueCoordinate], List[UniqueCoordinate]], **kwargs
    ) -> List[PairwiseDistance]:
        """
        This method computes pairwise distances between two sets of coordinates
        by slicing up the first set into smaller chunks. It returns a list of PairwiseDistance objects.
        """
        set1, set2 = data
        n_chunks = kwargs.get("n_chunks", DEFAULT_N_CHUNKS)
        chunk_size = math.ceil(len(set1) / n_chunks)
        pairs = []
        iterable = pb(range(n_chunks)) if self.progress_bar else range(n_chunks)
        for i in iterable:
            start = i * chunk_size
            end = start + chunk_size
            if len(set1[start:end]) == 0:
                continue
            pairs.extend(self.run((set1[start:end], set2), progress_bar=False))
        return pairs
