"use client";

import React, { useEffect, useRef } from "react";
import { Spinner } from "./ui";

interface SimpleVisualizationProps {
  components: any[];
  relationships: any[];
  onNodeClick?: (nodeId: string) => void;
  onComponentClick?: (componentData: any) => void;
  isProcessing?: boolean;
  svgString?: string;
}

// Add additional logging function
const logDebug = (message: string, data?: any) => {
  console.log(
    `[SimpleVisualization] ${message}`,
    data !== undefined ? data : ""
  );
};

const SimpleVisualization: React.FC<SimpleVisualizationProps> = ({
  components,
  relationships,
  onNodeClick,
  onComponentClick,
  isProcessing = false,
  svgString,
}) => {
  const svgContainerRef = useRef<HTMLDivElement>(null);

  // New useEffect to log components on mount for debugging
  useEffect(() => {
    if (components && components.length > 0) {
      logDebug(`Received ${components.length} components:`, components[0].id);
    }
  }, [components]);

  useEffect(() => {
    const container = svgContainerRef.current;
    if (!svgString || !container || !(onNodeClick || onComponentClick)) return;

    // Log that we're attaching event handlers for debugging
    logDebug("Setting up click handlers on SVG");

    const handleSvgClick = (event: MouseEvent) => {
      const target = event.target as Element;
      logDebug(`SVG Element Clicked:`, target.outerHTML);

      // Try to find the component group and extract data
      const targetGroup = target.closest("g[data-component-id]");

      if (targetGroup) {
        // Try to get the embedded component data first
        const embeddedDataStr = targetGroup.getAttribute("data-component-data");
        if (embeddedDataStr) {
          try {
            // Parse the JSON data embedded in the SVG
            const componentData = JSON.parse(embeddedDataStr);
            logDebug("Found embedded component data:", componentData);

            // If we have the direct component click handler, use it first
            if (onComponentClick) {
              logDebug("Directly passing component data to onComponentClick");
              onComponentClick(componentData);
              return;
            }

            // Fall back to ID-based callback if that's all we have
            if (componentData.id && onNodeClick) {
              logDebug("Using embedded component data - ID:", componentData.id);
              onNodeClick(componentData.id);
              return;
            }
          } catch (e) {
            logDebug("Error parsing embedded component data:", e);
          }
        }

        // Fallback to just the ID if embedded data isn't available
        const componentId = targetGroup.getAttribute("data-component-id");
        if (componentId && onNodeClick) {
          logDebug(`Found component ID from group:`, componentId);
          onNodeClick(componentId);
          return;
        }
      }

      // If we get here, try other fallback methods
      if (target.tagName === "rect" || target.tagName === "text") {
        // Try to get ID from rect or other element attributes
        const componentId =
          target.getAttribute("data-id") ||
          target.getAttribute("data-component-id") ||
          target.id;

        if (componentId) {
          logDebug(`Found component ID from element attribute:`, componentId);
          onNodeClick && onNodeClick(componentId);
          return;
        }

        // Last resort: try to match by position
        if (components.length > 0) {
          const y = parseInt(target.getAttribute("y") || "0");
          const verticalSpacing = 130; // Approximate spacing between components
          const estimatedIndex = Math.floor(y / verticalSpacing);

          if (estimatedIndex >= 0 && estimatedIndex < components.length) {
            const componentId = components[estimatedIndex].id;
            logDebug(`Matched component by position (y=${y}):`, componentId);
            onNodeClick && onNodeClick(componentId);
            return;
          }
        }
      }

      // Final fallback: use first component if available
      if (components && components.length > 0) {
        const componentId = components[0].id;
        logDebug(
          "No component ID found, using first component as fallback:",
          componentId
        );
        onNodeClick && onNodeClick(componentId);
      } else {
        logDebug("Could not determine component ID from click");
      }
    };

    container.addEventListener("click", handleSvgClick);

    return () => {
      if (container) {
        container.removeEventListener("click", handleSvgClick);
      }
    };
  }, [svgString, onNodeClick, onComponentClick, components]);

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
            onClick={() => {
              // If we have the component click handler, use it directly
              if (onComponentClick) {
                logDebug(
                  "Calling onComponentClick with component data:",
                  component.name
                );
                onComponentClick(component);
              } else if (onNodeClick) {
                // Fall back to node click handler with component ID
                logDebug(
                  "Calling onNodeClick with component ID:",
                  component.id
                );
                onNodeClick(component.id);
              }
            }}
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
