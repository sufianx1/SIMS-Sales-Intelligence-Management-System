import React from 'react';
import Plot from './Plot';

interface BarChartProps {
  x: (string | number)[];
  y: (string | number)[];
  title?: string;
  orientation?: 'v' | 'h';
  color?: string;
  height?: number;
}

export const BarChart: React.FC<BarChartProps> = ({
  x,
  y,
  title,
  orientation = 'v',
  color = '#2563eb',
  height = 300,
}) => {
  return (
    <Plot
      data={[
        {
          x: orientation === 'v' ? x : y,
          y: orientation === 'v' ? y : x,
          type: 'bar',
          orientation,
          marker: { color, opacity: 0.9 },
        },
      ]}
      layout={{
        title: title ? { text: title, font: { size: 14, family: 'Inter, sans-serif' } } : undefined,
        autosize: true,
        height,
        margin: { l: orientation === 'h' ? 140 : 40, r: 20, t: title ? 35 : 15, b: 40 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        xaxis: { gridcolor: '#f1f5f9', zerolinecolor: '#e2e8f0' },
        yaxis: { gridcolor: '#f1f5f9', zerolinecolor: '#e2e8f0' },
      }}
      useResizeHandler
      style={{ width: '100%', height: '100%' }}
      config={{ responsive: true, displayModeBar: false }}
    />
  );
};
