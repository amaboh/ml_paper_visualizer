"use client";

import React from "react";
import { Spinner } from "./ui";

interface SimpleVisualizationProps {
  components: any[];
  relationships: any[];
  onNodeClick?: (nodeId: string) => void;
  isProcessing?: boolean;
}

const SimpleVisualization: React.FC<SimpleVisualizationProps> = ({
  components,
  relationships,
  onNodeClick,
  isProcessing = false,
}) => {
  if (isProcessing) {
    return (
      <div className="flex flex-col items-center justify-center p-4 h-full">
        <Spinner size="lg" />
        <p className="mt-4 text-gray-600">
          Processing paper and generating visualization...
        </p>
      </div>
    );
  }

  if (!components || components.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        No components to visualize
      </div>
    );
  }

  // Generate a simple color for each component type
  const getColorForType = (type: string) => {
    const colors: Record<string, string> = {
      data_collection: "bg-emerald-500",
      preprocessing: "bg-indigo-500",
      data_partition: "bg-amber-500",
      model: "bg-red-500",
      training: "bg-purple-500",
      evaluation: "bg-pink-500",
      results: "bg-sky-500",
    };

    return colors[type] || "bg-gray-500";
  };

  return (
    <div className="p-4">
      <div className="flex flex-col items-center gap-4">
        {components.map((component) => (
          <div
            key={component.id}
            className={`p-4 rounded-lg shadow-md w-64 cursor-pointer ${getColorForType(
              component.type
            )} text-white`}
            onClick={() => onNodeClick && onNodeClick(component.name)}
          >
            <h3 className="font-bold">{component.name}</h3>
            <p className="text-sm opacity-80">{component.description}</p>
          </div>
        ))}
      </div>

      <div className="mt-8 p-4 bg-gray-100 rounded-lg">
        <h4 className="font-medium mb-2">Relationships</h4>
        <ul className="text-sm">
          {relationships.map((rel) => (
            <li key={rel.id} className="mb-1">
              {rel.description}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default SimpleVisualization;
