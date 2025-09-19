import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/alert';
import { AlertTriangle, TrendingUp, TrendingDown, Minus, Activity } from 'lucide-react';

const TradingDashboard = () => {
  const [signals, setSignals] = useState({});
  const [summaryData, setSummaryData] = useState({});
  const [selectedTimeframe, setSelectedTimeframe] = useState('M15');
  
  // Mock data - replace with your real data source
  const timeframes = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1'];
  const symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD'];
  
  // Signal types that match your indicator categories
  const indicatorTypes = [
    'RSI', 'MACD', 'Stoch', 'CCI', 'Williams%R', 'Ultimate Osc',
    'ROC', 'Bull/Bear Power', 'Ichimoku', 'VWAP', 'HVF', 'UO'
  ];

  // Generate mock signal data
  useEffect(() => {
    const generateSignalData = () => {
      const newSignals = {};
      const newSummary = {};
      
      symbols.forEach(symbol => {
        newSignals[symbol] = {};
        newSummary[symbol] = {};
        
        timeframes.forEach(tf => {
          newSignals[symbol][tf] = {};
          
          // Generate individual indicator signals
          indicatorTypes.forEach(indicator => {
            const rand = Math.random();
            let signal = 'No Signal';
            if (rand < 0.15) signal = 'Strong Sell';
            else if (rand < 0.3) signal = 'Weak Sell';
            else if (rand < 0.7) signal = 'No Signal';
            else if (rand < 0.85) signal = 'Weak Buy';
            else signal = 'Strong Buy';
            
            newSignals[symbol][tf][indicator] = signal;
          });
          
          // Calculate summary for this timeframe
          const signals = Object.values(newSignals[symbol][tf]);
          const buySignals = signals.filter(s => s.includes('Buy')).length;
          const sellSignals = signals.filter(s => s.includes('Sell')).length;
          const totalSignals = buySignals + sellSignals;
          
          let summary = 'No Signal';
          let confidence = 0;
          
          if (totalSignals > 0) {
            confidence = Math.round((Math.max(buySignals, sellSignals) / totalSignals) * 100);
            if (buySignals > sellSignals) {
              summary = confidence > 70 ? 'Strong Buy' : 'Buy';
            } else {
              summary = confidence > 70 ? 'Strong Sell' : 'Sell';
            }
          }
          
          newSummary[symbol][tf] = { summary, confidence, buySignals, sellSignals };
        });
      });
      
      setSignals(newSignals);
      setSummaryData(newSummary);
    };

    generateSignalData();
    const interval = setInterval(generateSignalData, 5000); // Update every 5 seconds
    
    return () => clearInterval(interval);
  }, []);

  const getSignalColor = (signal) => {
    switch (signal) {
      case 'Strong Buy': return 'bg-green-600 text-white';
      case 'Weak Buy': 
      case 'Buy': return 'bg-green-400 text-white';
      case 'Strong Sell': return 'bg-red-600 text-white';
      case 'Weak Sell':
      case 'Sell': return 'bg-red-400 text-white';
      default: return 'bg-gray-300 text-gray-700';
    }
  };

  const getSignalIcon = (signal) => {
    if (signal.includes('Buy')) return <TrendingUp className="w-3 h-3" />;
    if (signal.includes('Sell')) return <TrendingDown className="w-3 h-3" />;
    return <Minus className="w-3 h-3" />;
  };

  const ProgressBar = ({ value, type }) => {
    const width = Math.abs(value);
    const color = type === 'buy' ? 'bg-green-500' : 'bg-red-500';
    const direction = value >= 0 ? 'left' : 'right';
    
    return (
      <div className="w-full h-4 bg-gray-200 rounded relative overflow-hidden">
        <div 
          className={`h-full ${color} transition-all duration-300`}
          style={{ 
            width: `${width}%`,
            marginLeft: direction === 'right' ? 'auto' : '0'
          }}
        />
        <div className="absolute inset-0 flex items-center justify-center text-xs font-semibold text-gray-800">
          {value}%
        </div>
      </div>
    );
  };

  const SignalMatrix = () => (
    <div className="space-y-4">
      {/* Timeframe Selector */}
      <div className="flex gap-2 mb-4">
        {timeframes.map(tf => (
          <button
            key={tf}
            onClick={() => setSelectedTimeframe(tf)}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              selectedTimeframe === tf 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
            }`}
          >
            {tf}
          </button>
        ))}
      </div>

      {/* Signal Matrix */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse border border-gray-300">
          <thead>
            <tr className="bg-gray-100">
              <th className="border border-gray-300 p-2 text-left font-semibold">Symbol</th>
              {indicatorTypes.map(indicator => (
                <th key={indicator} className="border border-gray-300 p-1 text-xs font-medium min-w-16">
                  {indicator}
                </th>
              ))}
              <th className="border border-gray-300 p-2 text-left font-semibold">Summary</th>
              <th className="border border-gray-300 p-2 text-left font-semibold">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {symbols.map(symbol => {
              const symbolSignals = signals[symbol]?.[selectedTimeframe] || {};
              const summary = summaryData[symbol]?.[selectedTimeframe] || {};
              
              return (
                <tr key={symbol} className="hover:bg-gray-50">
                  <td className="border border-gray-300 p-2 font-medium">{symbol}</td>
                  {indicatorTypes.map(indicator => {
                    const signal = symbolSignals[indicator] || 'No Signal';
                    return (
                      <td key={indicator} className="border border-gray-300 p-1">
                        <div className={`rounded px-1 py-0.5 text-xs flex items-center justify-center gap-1 ${getSignalColor(signal)}`}>
                          {getSignalIcon(signal)}
                          <span className="hidden sm:inline">{signal.replace(' ', '')}</span>
                        </div>
                      </td>
                    );
                  })}
                  <td className="border border-gray-300 p-2">
                    <div className={`rounded px-2 py-1 text-sm font-medium flex items-center gap-1 ${getSignalColor(summary.summary)}`}>
                      {getSignalIcon(summary.summary)}
                      {summary.summary}
                    </div>
                  </td>
                  <td className="border border-gray-300 p-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{summary.confidence}%</span>
                      <ProgressBar 
                        value={summary.summary?.includes('Buy') ? summary.confidence : -summary.confidence} 
                        type={summary.summary?.includes('Buy') ? 'buy' : 'sell'}
                      />
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );

  const SummaryPanel = () => {
    const overallSummary = symbols.reduce((acc, symbol) => {
      Object.keys(summaryData[symbol] || {}).forEach(tf => {
        const data = summaryData[symbol][tf];
        if (data.summary.includes('Buy')) {
          acc.totalBuy += data.buySignals;
        } else if (data.summary.includes('Sell')) {
          acc.totalSell += data.sellSignals;
        }
      });
      return acc;
    }, { totalBuy: 0, totalSell: 0 });

    const total = overallSummary.totalBuy + overallSummary.totalSell;
    const buyPercentage = total > 0 ? Math.round((overallSummary.totalBuy / total) * 100) : 0;
    const sellPercentage = total > 0 ? Math.round((overallSummary.totalSell / total) * 100) : 0;

    return (
      <Card className="mb-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Market Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <div className="text-sm text-gray-600">Short-term Outlook</div>
              <ProgressBar value={buyPercentage - sellPercentage} type={buyPercentage > sellPercentage ? 'buy' : 'sell'} />
            </div>
            <div className="space-y-2">
              <div className="text-sm text-gray-600">Buy Signals</div>
              <div className="text-2xl font-bold text-green-600">{overallSummary.totalBuy}</div>
            </div>
            <div className="space-y-2">
              <div className="text-sm text-gray-600">Sell Signals</div>
              <div className="text-2xl font-bold text-red-600">{overallSummary.totalSell}</div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Trading Signals Dashboard</h1>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Activity className="w-4 h-4 animate-pulse text-green-500" />
            Real-time updates
          </div>
        </div>
        
        <SummaryPanel />
        
        <Card>
          <CardHeader>
            <CardTitle>Signal Matrix - {selectedTimeframe}</CardTitle>
          </CardHeader>
          <CardContent>
            <SignalMatrix />
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default TradingDashboard;