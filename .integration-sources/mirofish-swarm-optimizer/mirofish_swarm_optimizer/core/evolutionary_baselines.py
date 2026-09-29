"""Evolutionary Algorithm & Heuristic Baselines (GA & PSO) for Benchmarking."""
import random
import time
from typing import List, Dict, Set, Tuple, Optional
from .models import SwarmAgent, Coalition, CoalitionStructureResult, InfluenceResult, ConsensusRankingResult
from .coalition_structure import compute_coalition_value
from .kemeny_consensus import kendall_tau_distance

class GeneticAlgorithmCSG:
    """
    Standard Genetic Algorithm baseline for Coalition Structure Generation.
    Uses chromosome partition encoding, roulette-wheel selection, and mutation.
    """

    def __init__(
        self,
        agents: List[SwarmAgent],
        population_size: int = 40,
        generations: int = 50,
        mutation_rate: float = 0.15
    ):
        self.agents = agents
        self.agent_map = {a.agent_id: a for a in agents}
        self.n = len(agents)
        self.agent_ids = [a.agent_id for a in agents]
        self.pop_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate

    def solve(self, seed: int = 42) -> CoalitionStructureResult:
        t_start = time.perf_counter_ns()
        rng = random.Random(seed)

        n = self.n
        # Chromosome representation: list of length n, where gene[i] in [0, n-1] is coalition index
        def random_chromosome():
            return [rng.randint(0, n - 1) for _ in range(n)]

        def evaluate(chrom: List[int]) -> float:
            coalition_bins: Dict[int, List[str]] = {}
            for i, c_idx in enumerate(chrom):
                coalition_bins.setdefault(c_idx, []).append(self.agent_ids[i])
            welfare = sum(compute_coalition_value(tuple(m), self.agent_map) for m in coalition_bins.values())
            return welfare

        population = [random_chromosome() for _ in range(self.pop_size)]
        fitnesses = [evaluate(ind) for ind in population]

        best_score = max(fitnesses)
        best_chrom = population[fitnesses.index(best_score)]

        for _ in range(self.generations):
            new_population = []
            # Elitism: retain top 2
            elite_indices = sorted(range(self.pop_size), key=lambda idx: -fitnesses[idx])[:2]
            for e_idx in elite_indices:
                new_population.append(list(population[e_idx]))

            # Generate rest of population
            while len(new_population) < self.pop_size:
                # Tournament selection
                i1, i2 = rng.sample(range(self.pop_size), 2)
                p1 = population[i1] if fitnesses[i1] >= fitnesses[i2] else population[i2]
                i3, i4 = rng.sample(range(self.pop_size), 2)
                p2 = population[i3] if fitnesses[i3] >= fitnesses[i4] else population[i4]

                # Uniform crossover
                child = [p1[k] if rng.random() < 0.5 else p2[k] for k in range(n)]

                # Mutation
                for k in range(n):
                    if rng.random() < self.mutation_rate:
                        child[k] = rng.randint(0, n - 1)

                new_population.append(child)

            population = new_population
            fitnesses = [evaluate(ind) for ind in population]
            gen_best = max(fitnesses)
            if gen_best > best_score:
                best_score = gen_best
                best_chrom = population[fitnesses.index(gen_best)]

        # Decode best chromosome into coalitions
        bins: Dict[int, List[str]] = {}
        for i, c_idx in enumerate(best_chrom):
            bins.setdefault(c_idx, []).append(self.agent_ids[i])

        coalitions = [
            Coalition(members=tuple(m), value=compute_coalition_value(tuple(m), self.agent_map), internal_synergy=1.0)
            for m in bins.values()
        ]

        t_end = time.perf_counter_ns()
        return CoalitionStructureResult(
            coalitions=coalitions,
            total_welfare=best_score,
            algorithm=f"Genetic Algorithm (Pop: {self.pop_size}, Gen: {self.generations})",
            execution_time_us=(t_end - t_start) / 1000.0,
            iterations=self.generations
        )

class ParticleSwarmInfluenceMaximizer:
    """
    Standard Particle Swarm Optimization (PSO) baseline for Seed Selection.
    Uses continuous velocity updates mapped via sigmoid to binary seed masks.
    """

    def __init__(
        self,
        agents: List[SwarmAgent],
        adjacency: Dict[str, List[Tuple[str, float]]],
        swarm_size: int = 30,
        iterations: int = 35
    ):
        self.agents = agents
        self.agent_map = {a.agent_id: a for a in agents}
        self.nodes = [a.agent_id for a in agents]
        self.adj = adjacency
        self.n = len(self.nodes)
        self.swarm_size = swarm_size
        self.iterations = iterations

    def solve(self, k_seeds: int = 3, seed: int = 42) -> InfluenceResult:
        t_start = time.perf_counter_ns()
        rng = random.Random(seed)
        k_seeds = min(k_seeds, self.n)

        # Simulation evaluator: simple Monte Carlo spread estimation
        def estimate_spread(seeds: Set[str], trials: int = 20) -> float:
            total_active = 0
            for _ in range(trials):
                active = set(seeds)
                queue = list(seeds)
                while queue:
                    curr = queue.pop(0)
                    for neighbor, prob in self.adj.get(curr, []):
                        if neighbor not in active:
                            if rng.random() <= prob:
                                active.add(neighbor)
                                queue.append(neighbor)
                total_active += len(active)
            return total_active / trials

        # Initialize particles: continuous vectors of length n
        particles = [[rng.uniform(-2.0, 2.0) for _ in range(self.n)] for _ in range(self.swarm_size)]
        velocities = [[rng.uniform(-0.5, 0.5) for _ in range(self.n)] for _ in range(self.swarm_size)]
        pbest = [list(p) for p in particles]

        def get_top_k_seeds(particle: List[float]) -> Set[str]:
            top_indices = sorted(range(self.n), key=lambda idx: -particle[idx])[:k_seeds]
            return set(self.nodes[idx] for idx in top_indices)

        pbest_scores = [estimate_spread(get_top_k_seeds(p)) for p in particles]
        gbest_idx = pbest_scores.index(max(pbest_scores))
        gbest = list(pbest[gbest_idx])
        gbest_score = pbest_scores[gbest_idx]

        # PSO Parameters
        w = 0.7   # inertia
        c1 = 1.4  # cognitive
        c2 = 1.4  # social

        for _ in range(self.iterations):
            for i in range(self.swarm_size):
                for d in range(self.n):
                    r1 = rng.random()
                    r2 = rng.random()
                    v = (w * velocities[i][d] +
                         c1 * r1 * (pbest[i][d] - particles[i][d]) +
                         c2 * r2 * (gbest[d] - particles[i][d]))
                    # Velocity clamp
                    v = max(-3.0, min(3.0, v))
                    velocities[i][d] = v
                    particles[i][d] += v

                # Evaluate current position
                seeds = get_top_k_seeds(particles[i])
                score = estimate_spread(seeds)
                if score > pbest_scores[i]:
                    pbest_scores[i] = score
                    pbest[i] = list(particles[i])
                    if score > gbest_score:
                        gbest_score = score
                        gbest = list(particles[i])

        final_seeds = list(get_top_k_seeds(gbest))
        t_end = time.perf_counter_ns()

        return InfluenceResult(
            seed_agents=final_seeds,
            expected_reach=gbest_score,
            activation_percentage=(gbest_score / self.n) * 100.0,
            algorithm=f"Particle Swarm Optimization (Swarm: {self.swarm_size}, Iter: {self.iterations})",
            execution_time_us=(t_end - t_start) / 1000.0
        )
