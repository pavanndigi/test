"""Time a command N times and report wall seconds and peak RSS (children)."""
import resource, subprocess, sys, time, json
label, n, cmd = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
times = []
for _ in range(n):
    t0 = time.perf_counter()
    p = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    times.append(round(time.perf_counter() - t0, 3))
rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
print(json.dumps({"label": label, "rc": p.returncode, "wall_s": times, "median_s": sorted(times)[len(times)//2], "peak_rss_mb": round(rss/1024, 1)}))
