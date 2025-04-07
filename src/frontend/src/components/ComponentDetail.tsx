"use client";

import React from "react";
import { Card } from "./ui";

interface ComponentData {
  id: string;
  type: string;
  name: string;
  description: string;
  source_section?: string;
  source_page?: number;
  details?: Record<string, any>;
}

interface ComponentDetailProps {
  component: ComponentData | null;
}

const ComponentDetail: React.FC<ComponentDetailProps> = ({ component }) => {
  if (!component) {
    return (
      <Card className="h-full flex items-center justify-center">
        <p className="text-gray-500">Select a component to view details</p>
      </Card>
    );
  }

  // Format type for display
  const formatType = (type: string) => {
    return type
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  // Get badge color based on component type
  const getBadgeColor = (type: string) => {
    const colors: Record<string, string> = {
      data_collection: "bg-emerald-100 text-emerald-800",
      preprocessing: "bg-indigo-100 text-indigo-800",
      data_partition: "bg-amber-100 text-amber-800",
      model: "bg-red-100 text-red-800",
      training: "bg-purple-100 text-purple-800",
      evaluation: "bg-pink-100 text-pink-800",
      results: "bg-sky-100 text-sky-800",
    };

    return colors[type] || "bg-gray-100 text-gray-800";
  };

  // Helper function to render details as a list
  const renderDetails = (details: Record<string, any>) => {
    return Object.entries(details).map(([key, value]) => {
      const formattedKey = key
        .split("_")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");

      // Check if the value is an array
      if (Array.isArray(value)) {
        return (
          <div key={key} className="mb-3">
            <h4 className="font-medium text-sm text-gray-700">
              {formattedKey}:
            </h4>
            <ul className="list-disc pl-5 text-sm">
              {value.map((item, index) => (
                <li key={index} className="text-gray-600">
                  {typeof item === "object" ? JSON.stringify(item) : item}
                </li>
              ))}
            </ul>
          </div>
        );
      }

      // If value is an object, display as JSON
      if (typeof value === "object" && value !== null) {
        return (
          <div key={key} className="mb-3">
            <h4 className="font-medium text-sm text-gray-700">
              {formattedKey}:
            </h4>
            <pre className="bg-gray-50 p-2 rounded text-xs overflow-auto max-h-32">
              {JSON.stringify(value, null, 2)}
            </pre>
          </div>
        );
      }

      // For simple values
      return (
        <div key={key} className="mb-3">
          <h4 className="font-medium text-sm text-gray-700">{formattedKey}:</h4>
          <p className="text-sm text-gray-600">{value}</p>
        </div>
      );
    });
  };

  return (
    <Card className="h-full overflow-auto">
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            {component.name}
          </h3>
          <span
            className={`px-2 py-1 rounded-full text-xs font-medium ${getBadgeColor(
              component.type
            )}`}
          >
            {formatType(component.type)}
          </span>
        </div>

        <div className="mb-4">
          <h4 className="font-medium text-sm text-gray-700">Description:</h4>
          <p className="text-sm text-gray-600">{component.description}</p>
        </div>

        {component.source_section && (
          <div className="mb-4">
            <h4 className="font-medium text-sm text-gray-700">
              Source Section:
            </h4>
            <p className="text-sm text-gray-600">{component.source_section}</p>
          </div>
        )}

        {component.source_page && (
          <div className="mb-4">
            <h4 className="font-medium text-sm text-gray-700">Source Page:</h4>
            <p className="text-sm text-gray-600">{component.source_page}</p>
          </div>
        )}

        {component.details && Object.keys(component.details).length > 0 && (
          <div className="mt-6">
            <h4 className="font-medium text-gray-700 mb-3">
              Technical Details:
            </h4>
            <div className="bg-gray-50 p-4 rounded">
              {renderDetails(component.details)}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

export default ComponentDetail;
