import React, { useState, useEffect } from 'react';
import { Upload, AlertCircle } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Alert, AlertDescription } from '@/components/ui/alert';

const ArtifactAnalyzer = () => {
  const [files, setFiles] = useState([]);
  const [results, setResults] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);

  // Artifact class definitions based on GrandQC
  const artifactClasses = {
    1: { name: "Normal Tissue", color: "rgb(128, 128, 128)" },
    2: { name: "Tissue Fold", color: "rgb(255, 99, 71)" },
    3: { name: "Dark Spot/Foreign", color: "rgb(0, 255, 0)" },
    4: { name: "Pen Marking", color: "rgb(255, 0, 0)" },
    5: { name: "Air Bubble/Edge", color: "rgb(255, 0, 255)" },
    6: { name: "Out of Focus", color: "rgb(75, 0, 130)" },
  };

  const analyzeMask = async (file) => {
    try {
      // Create canvas to process image data
      const img = new Image();
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      return new Promise((resolve) => {
        img.onload = () => {
          canvas.width = img.width;
          canvas.height = img.height;
          ctx.drawImage(img, 0, 0);
          
          const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
          const pixels = imageData.data;
          
          // Count pixels for each class
          const counts = new Array(7).fill(0);
          for (let i = 0; i < pixels.length; i += 4) {
            const value = pixels[i]; // Using red channel as class indicator
            if (value < 7) { // Valid class
              counts[value]++;
            }
          }
          
          // Calculate percentages
          const totalTissuePixels = counts.reduce((sum, count, idx) => 
            idx !== 6 ? sum + count : sum, 0);
          
          const percentages = counts.map(count => 
            ((count / totalTissuePixels) * 100).toFixed(2));
          
          resolve({
            filename: file.name,
            percentages: percentages,
            totalPixels: totalTissuePixels
          });
        };
        img.src = URL.createObjectURL(file);
      });
    } catch (err) {
      console.error("Error analyzing mask:", err);
      throw err;
    }
  };

  const handleFileUpload = async (event) => {
    const uploadedFiles = Array.from(event.target.files);
    setFiles(uploadedFiles);
    setError(null);
    setIsProcessing(true);

    try {
      const analysisResults = await Promise.all(
        uploadedFiles.map(file => analyzeMask(file))
      );
      setResults(analysisResults);
    } catch (err) {
      setError("Error processing images. Please ensure you're uploading valid mask files.");
    } finally {
      setIsProcessing(false);
    }
  };

  const downloadCSV = () => {
    if (results.length === 0) return;

    const headers = [
      "Filename",
      ...Object.values(artifactClasses).map(c => c.name),
      "Total Pixels"
    ];

    const csvContent = [
      headers.join(","),
      ...results.map(result => [
        result.filename,
        ...result.percentages,
        result.totalPixels
      ].join(","))
    ].join("\n");

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'artifact_analysis.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-6 space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold">GrandQC Artifact Analyzer</h1>
        <p className="text-gray-600">
          Upload mask images to analyze artifact percentages
        </p>
      </div>

      {/* Upload Section */}
      <div className="flex flex-col items-center space-y-4">
        <label className="relative cursor-pointer bg-white border-2 border-dashed border-gray-300 rounded-lg p-12 hover:border-gray-400 transition-colors">
          <input
            type="file"
            multiple
            accept="image/*"
            onChange={handleFileUpload}
            className="hidden"
          />
          <div className="text-center space-y-2">
            <Upload className="mx-auto h-12 w-12 text-gray-400" />
            <div className="text-gray-600">
              Click to upload mask images or drag and drop
            </div>
          </div>
        </label>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Results Section */}
      {results.length > 0 && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-semibold">Analysis Results</h2>
            <button
              onClick={downloadCSV}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Download CSV
            </button>
          </div>

          {/* Results Chart */}
          <div className="h-96 bg-white p-4 rounded-lg shadow">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={results.map((result, idx) => ({
                name: result.filename,
                ...Object.keys(artifactClasses).reduce((acc, key) => ({
                  ...acc,
                  [artifactClasses[key].name]: parseFloat(result.percentages[key-1])
                }), {})
              }))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis label={{ value: 'Percentage', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                {Object.entries(artifactClasses).map(([key, value]) => (
                  <Line
                    key={key}
                    type="monotone"
                    dataKey={value.name}
                    stroke={value.color}
                    strokeWidth={2}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Results Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left text-gray-500">
              <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                <tr>
                  <th className="px-6 py-3">Filename</th>
                  {Object.values(artifactClasses).map(c => (
                    <th key={c.name} className="px-6 py-3">{c.name} (%)</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {results.map((result, idx) => (
                  <tr key={idx} className="bg-white border-b hover:bg-gray-50">
                    <td className="px-6 py-4 font-medium text-gray-900">
                      {result.filename}
                    </td>
                    {result.percentages.slice(0, 6).map((percentage, pidx) => (
                      <td key={pidx} className="px-6 py-4">
                        {percentage}%
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default ArtifactAnalyzer;