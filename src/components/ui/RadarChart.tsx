import React from 'react';
import {
  Radar,
  RadarChart as RechartsRadarChart,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
  Tooltip
} from 'recharts';

interface RadarChartProps {
  data: {
    category: string;
    score: number;
  }[];
  size?: 'small' | 'medium' | 'large';
}

const RadarChart: React.FC<RadarChartProps> = ({ 
  data, 
  size = 'medium' 
}) => {
  // Calculate dimensions based on size
  const dimensions = {
    small: { width: 250, height: 200 },
    medium: { width: 350, height: 300 },
    large: { width: 450, height: 400 }
  };
  
  const { width, height } = dimensions[size];
  
  // Format data for the radar chart
  const formattedData = data.map(item => ({
    category: item.category.charAt(0).toUpperCase() + item.category.slice(1),
    score: item.score,
    fullMark: 5
  }));
  
  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-2 border rounded shadow-sm">
          <p className="font-medium">{`${payload[0].payload.category}: ${payload[0].value.toFixed(1)}/5`}</p>
        </div>
      );
    }
    return null;
  };
  
  return (
    <div style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsRadarChart cx="50%" cy="50%" outerRadius="80%" data={formattedData}>
          <PolarGrid stroke="#e5e7eb" />
          <PolarAngleAxis dataKey="category" tick={{ fill: '#6b7280', fontSize: 12 }} />
          <Radar
            name="Score"
            dataKey="score"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.6}
          />
          <Tooltip content={<CustomTooltip />} />
        </RechartsRadarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default RadarChart;