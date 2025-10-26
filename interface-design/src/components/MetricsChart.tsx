import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface MetricsChartProps {
  data: Array<{
    epoch: number;
    mAP50: number;
    box_loss: number;
    precision: number;
    recall: number;
  }>;
}

export function MetricsChart({ data }: MetricsChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <span className="text-xl">📊</span>
          Evolução das Métricas
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-8">
          {/* mAP50 Chart */}
          <div>
            <h4 className="text-sm mb-4 text-muted-foreground">mAP50 por Época</h4>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis 
                  dataKey="epoch" 
                  label={{ value: 'Época', position: 'insideBottom', offset: -5 }}
                  className="text-xs"
                  stroke="hsl(var(--muted-foreground))"
                />
                <YAxis 
                  domain={[0, 1]} 
                  label={{ value: 'mAP50', angle: -90, position: 'insideLeft' }}
                  className="text-xs"
                  stroke="hsl(var(--muted-foreground))"
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    padding: '8px 12px'
                  }}
                  labelStyle={{ color: 'hsl(var(--foreground))' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="mAP50" 
                  stroke="hsl(221.2 83.2% 53.3%)" 
                  strokeWidth={3}
                  dot={false}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Loss Chart */}
          <div>
            <h4 className="text-sm mb-4 text-muted-foreground">Box Loss por Época</h4>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis 
                  dataKey="epoch" 
                  label={{ value: 'Época', position: 'insideBottom', offset: -5 }}
                  className="text-xs"
                  stroke="hsl(var(--muted-foreground))"
                />
                <YAxis 
                  label={{ value: 'Loss', angle: -90, position: 'insideLeft' }}
                  className="text-xs"
                  stroke="hsl(var(--muted-foreground))"
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    padding: '8px 12px'
                  }}
                  labelStyle={{ color: 'hsl(var(--foreground))' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="box_loss" 
                  stroke="hsl(142.1 76.2% 36.3%)" 
                  strokeWidth={3}
                  dot={false}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Precision & Recall Chart */}
          <div>
            <h4 className="text-sm mb-4 text-muted-foreground">Precision & Recall por Época</h4>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis 
                  dataKey="epoch" 
                  label={{ value: 'Época', position: 'insideBottom', offset: -5 }}
                  className="text-xs"
                  stroke="hsl(var(--muted-foreground))"
                />
                <YAxis 
                  domain={[0, 1]} 
                  className="text-xs"
                  stroke="hsl(var(--muted-foreground))"
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    padding: '8px 12px'
                  }}
                  labelStyle={{ color: 'hsl(var(--foreground))' }}
                />
                <Legend wrapperStyle={{ paddingTop: '20px' }} />
                <Line 
                  type="monotone" 
                  dataKey="precision" 
                  stroke="hsl(221.2 83.2% 53.3%)" 
                  strokeWidth={3}
                  dot={false}
                  name="Precision"
                  activeDot={{ r: 6 }}
                />
                <Line 
                  type="monotone" 
                  dataKey="recall" 
                  stroke="hsl(142.1 70.6% 45.3%)" 
                  strokeWidth={3}
                  dot={false}
                  name="Recall"
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}