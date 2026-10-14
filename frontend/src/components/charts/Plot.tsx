import Plotly from 'plotly.js-dist-min';
import createPlotlyComponent from 'react-plotly.js/factory';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const factory = (createPlotlyComponent as any).default || createPlotlyComponent;
export const Plot = factory(Plotly);
export default Plot;
