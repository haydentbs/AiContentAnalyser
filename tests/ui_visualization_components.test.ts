import { describe, it, expect } from 'vitest';
import GaugeChart from '../src/components/ui/GaugeChart';
import RadarChart from '../src/components/ui/RadarChart';
import MetricResultCard from '../src/components/ui/MetricResultCard';

describe('Visualization Components', () => {
  it('GaugeChart component exists', () => {
    expect(GaugeChart).toBeDefined();
  });

  it('RadarChart component exists', () => {
    expect(RadarChart).toBeDefined();
  });

  it('MetricResultCard component exists', () => {
    expect(MetricResultCard).toBeDefined();
  });
});