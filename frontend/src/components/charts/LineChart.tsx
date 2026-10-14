import React from 'react';
import Plot from './Plot';

interface LineChartProps {
  x: string[];
  y: number[];
  name?: string;
  title?: string;
  color?: string;
  height?: number;
}

export const LineChart: React.FC<LineChartProps> = ({
  x,
  y,
  name = 'Value',
  title,
  color = '#2563eb',
  height = 320,
}) => {
  return (
    <Plot
      data={[
        {
          x,
          y,
          type: 'scatter',
          mode: 'lines+markers',
          name,
          line: { color, width: 2.5 },
          marker: { color, size: 6 },
        },
      ]}
      layout={{
        title: title ? { text: title, font: { size: 14, family: 'Inter, sans-serif' } } : undefined,
        autosize: true,
        height,
        margin: { l: 50, r: 20, t: title ? 35 : 15, b: 40 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        xaxis: { gridcolor: '#f1f5f9' },
        yaxis: { gridcolor: '#f1f5f9' },
      }}
      useResizeHandler
      style={{ width: '100%', height: '100%' }}
      config={{ responsive: true, displayModeBar: false }}
    />
  );
};
