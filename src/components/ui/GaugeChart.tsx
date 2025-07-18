import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

interface GaugeChartProps {
  value: number; // Value between 0 and 5
  size?: 'small' | 'medium' | 'large';
  showLabel?: boolean;
}

const GaugeChart: React.FC<GaugeChartProps> = ({ 
  value, 
  size = 'medium',
  showLabel = true 
}) => {
  // Normalize value to percentage (0-100)
  const normalizedValue = (value / 5) * 100;
  
  // Calculate dimensions based on size
  const dimensions = {
    small: { width: 100, height: 60, fontSize: 14 },
    medium: { width: 160, height: 100, fontSize: 20 },
    large: { width: 200, height: 120, fontSize: 24 }
  };
  
  const { width, height, fontSize } = dimensions[size];
  
  // Data for the gauge chart
  const data = [
    { name: 'Score', value: normalizedValue },
    { name: 'Remaining', value: 100 - normalizedValue }
  ];
  
  // Colors based on score value
  const getColor = (score: number) => {
    if (score >= 80) return '#22c55e'; // Green for high scores
    if (score >= 60) return '#eab308'; // Yellow for medium scores
    if (score >= 40) return '#f97316'; // Orange for low-medium scores
    return '#ef4444'; // Red for low scores
  };
  
  const scoreColor = getColor(normalizedValue);
  
  return (
    <div style={{ width, height, position: 'relative' }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="100%"
            startAngle={180}
            endAngle={0}
            innerRadius="60%"
            outerRadius="100%"
            paddingAngle={0}
            dataKey="value"
            stroke="none"
          >
            <Cell key="score" fill={scoreColor} />
            <Cell key="remaining" fill="#e5e7eb" />
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      {showLabel && (
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -20%)',
            textAlign: 'center',
            fontSize: fontSize,
            fontWeight: 'bold',
            color: scoreColor
          }}
        >
          {value.toFixed(1)}
        </div>
      )}
    </div>
  );
};

export default GaugeChart;