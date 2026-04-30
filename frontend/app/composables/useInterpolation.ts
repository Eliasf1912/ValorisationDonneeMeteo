import type { NationalIndicatorDataPoint } from "~/types/api";

export function lerp(a: number, b: number, t: number): number {
    return a + t * (b - a);
}

/**
 * Inserts interpolated crossing points wherever temperature crosses baseline_mean.
 * At each crossing, temperature === baseline_mean, making the red/blue band areas
 * taper cleanly to zero instead of bleeding past the real intersection.
 */
export function insertCrossingPoints(
    series: NationalIndicatorDataPoint[],
): NationalIndicatorDataPoint[] {
    if (series.length < 2) return series;

    const result: NationalIndicatorDataPoint[] = [series[0]!];

    for (let i = 1; i < series.length; i++) {
        const prev = series[i - 1]!;
        const curr = series[i]!;
        const prevDiff = prev.temperature - prev.baseline_mean;
        const currDiff = curr.temperature - curr.baseline_mean;

        if (prevDiff * currDiff < 0) {
            // t ∈ (0,1) where the two lines intersect
            const t = prevDiff / (prevDiff - currDiff);
            const crossDate = new Date(
                new Date(prev.date).getTime() +
                    t *
                        (new Date(curr.date).getTime() -
                            new Date(prev.date).getTime()),
            );
            const crossValue = lerp(prev.temperature, curr.temperature, t);
            const baselineStdDevUpper: number = lerp(
                prev.baseline_std_dev_upper,
                curr.baseline_std_dev_upper,
                t,
            );
            const baselineStdDevLower: number = lerp(
                prev.baseline_std_dev_lower,
                curr.baseline_std_dev_lower,
                t,
            );
            result.push({
                date: crossDate.toISOString(),
                temperature: crossValue,
                baseline_mean: crossValue, // equal → bands are zero at this point
                baseline_std_dev_upper: baselineStdDevUpper,
                baseline_std_dev_lower: baselineStdDevLower,
                baseline_max: lerp(prev.baseline_max, curr.baseline_max, t),
                baseline_min: lerp(prev.baseline_min, curr.baseline_min, t),
                isInterpolated: true,
                is_hot_peak: crossValue > baselineStdDevUpper,
                is_cold_peak: crossValue < baselineStdDevLower,
            });
        }

        result.push(curr);
    }

    return result;
}
