"use client";

import React, { useEffect, useRef } from "react";
import { Spinner } from "./ui";

interface SimpleVisualizationProps {
  components: any[];
  relationships: any[];
  onNodeClick?: (nodeId: string) => void;
  isProcessing?: boolean;
  svgString?: string;
}

const SimpleVisualization: React.FC<SimpleVisualizationProps> = ({
  components,
  relationships,
  onNodeClick,
  isProcessing = false,
  svgString,
}) => {
  const svgContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = svgContainerRef.current;
    if (!svgString || !container || !onNodeClick) return;

    const handleSvgClick = (event: MouseEvent) => {
      let targetElement = event.target as SVGElement | null;
      while (
        targetElement &&
        targetElement.tagName !== "g" &&
        targetElement.tagName !== "svg"
      ) {
        targetElement = targetElement.parentElement as SVGElement | null;
      }

      const componentId = targetElement?.getAttribute("data-component-id");
      if (componentId) {
        onNodeClick(componentId);
      }
    };

    container.addEventListener("click", handleSvgClick);

    return () => {
      container.removeEventListener("click", handleSvgClick);
    };
  }, [svgString, onNodeClick]);

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

  if (svgString) {
    return (
      <div
        ref={svgContainerRef}
        className="w-full h-full flex items-center justify-center overflow-auto"
        dangerouslySetInnerHTML={{ __html: svgString }}
      />
    );
  }

  if (!components || components.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        No components to visualize (or SVG failed to load)
      </div>
    );
  }

  const getStylesForType = (type: string) => {
    const styles: Record<string, string> = {
      data_collection:
        "bg-emerald-50 border border-emerald-400 text-emerald-800",
      preprocessing: "bg-indigo-50 border border-indigo-400 text-indigo-800",
      data_partition: "bg-amber-50 border border-amber-400 text-amber-800",
      model: "bg-red-50 border border-red-400 text-red-800",
      training: "bg-purple-50 border border-purple-400 text-purple-800",
      evaluation: "bg-pink-50 border border-pink-400 text-pink-800",
      results: "bg-sky-50 border border-sky-400 text-sky-800",
      other: "bg-gray-100 border border-gray-400 text-gray-800",
    };
    return styles[type] || styles.other;
  };

  return (
    <div className="p-6 w-full max-w-2xl mx-auto flex flex-col items-center">
      {components.map((component, index) => (
        <React.Fragment key={component.id}>
          <div
            className={`relative p-4 rounded-lg shadow-md w-full sm:w-96 cursor-pointer transition-transform hover:scale-[1.02] mb-8 ${getStylesForType(
              component.type
            )} 
            ${
              index < components.length - 1
                ? "after:content-[''] after:absolute after:left-1/2 after:-bottom-8 after:h-8 after:w-0.5 after:bg-gray-300 after:-translate-x-1/2"
                : ""
            }`}
            onClick={() => onNodeClick && onNodeClick(component.id)}
          >
            <h3 className="font-bold text-center text-lg">{component.name}</h3>
            <p className="text-sm opacity-90 mt-2 text-center">
              {component.description}
            </p>
          </div>
        </React.Fragment>
      ))}
    </div>
  );
};

export default SimpleVisualization;
