# LLM Code Optimization Benchmark

A pattern-driven benchmark for evaluating LLM-based code optimization on real-world performance inefficiencies, with paired slow/optimized implementations and reproducible speedup + correctness metrics.

## Overview
Traditional compilers are conservative: when aliasing is unclear, control-flow is complex, or runtime data properties matter, many optimizations are hard to apply safely. This repo provides a benchmark suite designed to test whether large language models (LLMs) can **identify** and **optimize** these kinds of inefficiencies while preserving correctness.

The benchmark is organized around common inefficiency patterns observed in HPC/scientific/ML code. 
