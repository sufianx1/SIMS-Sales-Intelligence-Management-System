import React from 'react';
import Plot from './Plot';

interface PieChartProps {
  labels: string[];
  values: number[];
  title?: string;
  height?: number;
}

export const PieChart: React.FC<PieChartProps> = ({
  labels,
  values,
  title,
  height = 300,
}) => {
  return (
    <Plot
      data={[
        {
          labels,
          values,
          type: 'pie',
          hole: 0.4,
          marker: {
            colors: ['#2563eb', '#38bdf8', '#818cf8', '#34d399', '#f59e0b', '#f43f5e'],
          },
        },
      ]}
      layout={{
        title: title ? { text: title, font: { size: 14, family: 'Inter, sans-serif' } } : undefined,
        autosize: true,
        height,
        margin: { l: 20, r: 20, t: title ? 35 : 15, b: 20 },
        paper_bgcolor: 'transparent',
        showlegend: true,
        legend: { orientation: 'h', y: -0.1 },
      }}
      useResizeHandler
      style={{ width: '100%', height: '100%' }}
      config={{ responsive: true, displayModeBar: false }}
    />
  );
};
