/**
 * Tree-shakeable ECharts setup. Import `echarts` from this module instead of
 * `import * as echarts from 'echarts'` to avoid bundling unused chart types.
 */
import * as echarts from 'echarts/core';

import { BarChart, LineChart, PieChart, SankeyChart } from 'echarts/charts';
import {
  DatasetComponent,
  GridComponent,
  LegendComponent,
  TitleComponent,
  TooltipComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([
  BarChart,
  LineChart,
  PieChart,
  SankeyChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  DatasetComponent,
  CanvasRenderer,
]);

export default echarts;
export type { EChartsOption, ECharts } from 'echarts/core';
