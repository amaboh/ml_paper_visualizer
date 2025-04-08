"use client";

import React, { useState, useEffect, useRef } from "react";
import { Button, Card, Tabs, Spinner } from "../../../components/ui";
import {
  ArrowLeftIcon,
  DownloadIcon,
  CogIcon,
} from "../../../components/icons";
import { useRouter } from "next/navigation";
import SimpleVisualization from "../../../components/SimpleVisualization";
import MermaidDiagram from "../../../components/MermaidDiagram";
import D3Visualization from "../../../components/D3Visualization";
import ComponentDetail from "../../../components/ComponentDetail";

interface ResultsProps {
  params: {
    id: string;
  };
}

interface DiagnosticsStage {
  status: string;
  error?: string;
}

interface DiagnosticsFileInfo {
  file_size_kb?: number;
  text_length?: number;
  content_type_extracted?: string;
}

interface DiagnosticsData {
  parser_used?: string;
  extraction_stages?: Record<string, DiagnosticsStage>;
  timings?: Record<string, number>;
  file_info?: DiagnosticsFileInfo;
  full_text_extracted?: string;
}

interface ErrorDetails {
  type?: string;
  message?: string;
}

interface PaperData {
  id: string;
  title: string;
  status: "uploaded" | "processing" | "completed" | "failed";
  components?: ComponentData[];
  relationships?: RelationshipData[];
  paper_type?: string;
  visualization?: {
    diagram_type?: string;
    diagram_data?: string;
    component_mapping?: Record<string, string>;
  };
  diagnostics?: DiagnosticsData;
  error_message?: string;
  error_details?: ErrorDetails;
}

interface ComponentData {
  id: string;
  type: string;
  name: string;
  description: string;
  source_section?: string;
  source_page?: number;
  details?: Record<string, unknown>;
  children?: ComponentData[];
  parent?: string;
  _isExpanded?: boolean;
  metrics?: Record<string, number>;
  importance?: number;
  is_novel?: boolean;
}

interface RelationshipData {
  id: string;
  source_id: string;
  target_id: string;
  type: string;
  description: string;
}

interface D3Data {
  nodes: ComponentData[];
  links: LinkData[];
  hierarchical_nodes?: ComponentData[];
}

interface LinkData {
  source: string;
  target: string;
  type: string;
  description: string;
}

interface VisualizationSettings {
  showNodeLabels: boolean;
  showMetrics: boolean;
  highlightNovel: boolean;
  componentTypeFilters: string[];
  relationshipTypeFilters: string[];
}

export default function Results({ params }: ResultsProps): React.ReactNode {
  const { id } = params;
  const router = useRouter();
  const visualizationRef = useRef<HTMLDivElement>(null);

  const [paperData, setPaperData] = useState<PaperData | null>(null);
  const [selectedComponent, setSelectedComponent] =
    useState<ComponentData | null>(null);
  const [activeTab, setActiveTab] = useState<string>("details");
  const [visualizationType, setVisualizationType] = useState<string>("d3");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState<number>(0);
  const [pollingTimer, setPollingTimer] = useState<NodeJS.Timeout | null>(null);
  const [d3Data, setD3Data] = useState<D3Data | null>(null);
  const [mermaidChart, setMermaidChart] = useState<string>("");
  const [exportMenuOpen, setExportMenuOpen] = useState<boolean>(false);
  const [settingsOpen, setSettingsOpen] = useState<boolean>(false);
  const [settings, setSettings] = useState<VisualizationSettings>({
    showNodeLabels: true,
    showMetrics: true,
    highlightNovel: true,
    componentTypeFilters: [],
    relationshipTypeFilters: [],
  });

  // Get all available component and relationship types
  const [availableComponentTypes, setAvailableComponentTypes] = useState<
    string[]
  >([]);
  const [availableRelationshipTypes, setAvailableRelationshipTypes] = useState<
    string[]
  >([]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingTimer) {
        clearInterval(pollingTimer);
      }
    };
  }, [pollingTimer]);

  // Fetch paper data and status
  useEffect(() => {
    const fetchPaperData = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/papers/${id}`);

        if (response.status === 404) {
          setError(
            "Paper not found. It may have been deleted or the ID is incorrect."
          );
          setLoading(false);
          return;
        }

        if (!response.ok) {
          throw new Error(`Failed to fetch paper: ${response.statusText}`);
        }

        const data = await response.json();
        setPaperData(data);

        // Handle error status immediately
        if (data.status === "error" || data.status === "failed") {
          setLoading(false);

          // Set error based on error details or message
          if (data.error_details?.type === "EXTRACTION_CONTENT_TOO_SHORT") {
            setError(
              "The PDF content is too short to extract meaningful ML workflow components. Please try uploading a paper with more content."
            );
          } else if (data.error_message) {
            setError(data.error_message);
          } else if (data.error_details?.message) {
            setError(data.error_details.message);
          } else {
            setError(
              "Paper processing failed. The system couldn't extract ML workflow information."
            );
          }
          return;
        }

        // If completed, stop loading
        if (data.status === "completed") {
          setLoading(false);

          // Fetch visualization data
          await fetchVisualizationData();
        } else if (data.status === "processing") {
          // For processing, we show the visualization with processing state
          // but keep polling for updates
          setLoading(false);

          // Poll for updates if still processing
          const timer = setInterval(async () => {
            try {
              const statusResponse = await fetch(`/api/papers/${id}/status`);
              if (!statusResponse.ok) {
                throw new Error(
                  `Failed to fetch status: ${statusResponse.statusText}`
                );
              }

              const statusData = await statusResponse.json();

              // If status changed, update the paper data
              if (statusData.status !== paperData?.status) {
                // If new status is completed, fetch the full paper data
                if (statusData.status === "completed") {
                  const paperResponse = await fetch(`/api/papers/${id}`);
                  if (paperResponse.ok) {
                    const newPaperData = await paperResponse.json();
                    setPaperData(newPaperData);
                    await fetchVisualizationData();
                  }
                } else if (
                  statusData.status === "failed" ||
                  statusData.status === "error"
                ) {
                  // If failed or error, fetch the full paper data to get error details
                  const paperResponse = await fetch(`/api/papers/${id}`);
                  if (paperResponse.ok) {
                    const newPaperData = await paperResponse.json();
                    setPaperData(newPaperData);

                    // Set error based on error details, diagnostics, or a generic message
                    if (
                      newPaperData.error_details?.type ===
                      "EXTRACTION_CONTENT_TOO_SHORT"
                    ) {
                      setError(
                        "The PDF content is too short to extract meaningful ML workflow components. Please try uploading a paper with more content."
                      );
                    } else if (newPaperData.error_message) {
                      setError(newPaperData.error_message);
                    } else if (newPaperData.error_details?.message) {
                      setError(newPaperData.error_details.message);
                    } else {
                      setError(
                        "Paper processing failed. The system couldn't extract ML workflow information."
                      );
                    }
                  }
                } else {
                  // Otherwise just update the status
                  setPaperData((prev) =>
                    prev ? { ...prev, status: statusData.status } : null
                  );
                }
              }

              // Stop polling when processing is done
              if (
                statusData.status === "completed" ||
                statusData.status === "failed"
              ) {
                clearInterval(timer);
              }
            } catch (err) {
              console.error("Error polling paper status:", err);
              // Don't stop polling on temporary errors
            }
          }, 3000); // Poll every 3 seconds

          setPollingTimer(timer);
        } else if (data.status === "uploaded") {
          setError(
            "Paper is waiting to be processed. Please try again in a few moments."
          );
          setLoading(false);
        } else if (data.status === "failed") {
          // Get additional error details if available
          if (data.error_message) {
            setError(data.error_message);
          } else {
            setError(
              "Paper processing failed. The system couldn't extract ML workflow information."
            );
          }
          setLoading(false);
        }
      } catch (err) {
        console.error("Error fetching paper:", err);
        setError(err instanceof Error ? err.message : "Failed to load paper");
        setLoading(false);
      }
    };

    fetchPaperData();
  }, [id, retryCount]);

  // Fetch visualization data
  const fetchVisualizationData = async () => {
    try {
      // Fetch D3 visualization data
      const d3Response = await fetch(`/api/visualization/${id}/d3`);
      if (d3Response.ok) {
        const d3Data = await d3Response.json();
        setD3Data(d3Data);
      }

      // Fetch Mermaid visualization data
      const mermaidResponse = await fetch(`/api/visualization/${id}/mermaid`);
      if (mermaidResponse.ok) {
        const mermaidData = await mermaidResponse.json();
        setMermaidChart(mermaidData.diagram_data);
      }
    } catch (error) {
      console.error("Error fetching visualization data:", error);
    }
  };

  // Function to handle node click in the diagram
  const handleNodeClick = async (nodeId: string) => {
    if (!paperData || !paperData.components) return;

    try {
      const response = await fetch(`/api/papers/${id}/components/${nodeId}`);
      if (response.ok) {
        const componentData = await response.json();
        setSelectedComponent(componentData);
        setActiveTab("details");
      } else {
        // Fallback to finding component by ID in the current data
        const component = paperData.components.find((c) => c.id === nodeId);
        if (component) {
          setSelectedComponent(component);
          setActiveTab("details");
        }
      }
    } catch (err) {
      console.error("Error fetching component details:", err);
    }
  };

  const handleRetry = () => {
    setError(null);
    setRetryCount((prev) => prev + 1);
  };

  const handleBack = () => {
    router.push("/");
  };

  // Handle export functionality
  const handleExport = async (format: string) => {
    setExportMenuOpen(false);

    try {
      // Different export approaches based on visualization type
      if (visualizationType === "d3") {
        // For D3, we'll export the SVG directly from the DOM
        if (visualizationRef.current) {
          const svgElement = visualizationRef.current.querySelector("svg");
          if (svgElement) {
            const svgData = new XMLSerializer().serializeToString(svgElement);

            if (format === "svg") {
              // For SVG, create a download link
              downloadSvg(
                svgData,
                `${paperData?.title || "visualization"}.svg`
              );
            } else if (format === "png") {
              // For PNG, convert SVG to PNG
              await convertSvgToPng(
                svgData,
                `${paperData?.title || "visualization"}.png`
              );
            }
          }
        }
      } else if (visualizationType === "mermaid") {
        // For Mermaid, fetch a rendered version from the API
        const response = await fetch(
          `/api/visualization/${id}/export?format=${format}`
        );
        if (response.ok) {
          const data = await response.json();

          // Handle the exported data based on format
          if (format === "svg") {
            downloadSvg(
              data.data,
              `${paperData?.title || "visualization"}.svg`
            );
          } else if (format === "png") {
            // Download PNG directly if API provides it
            // otherwise convert SVG to PNG
            await convertSvgToPng(
              data.data,
              `${paperData?.title || "visualization"}.png`
            );
          }
        }
      } else {
        // For simple visualization, take a screenshot (not ideal but a fallback)
        alert(
          "Export is only supported for D3 and Mermaid visualizations currently"
        );
      }
    } catch (error) {
      console.error("Error exporting visualization:", error);
      alert("Failed to export visualization. Please try again.");
    }
  };

  // Download SVG helper
  const downloadSvg = (svgData: string, filename: string) => {
    const blob = new Blob([svgData], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Convert SVG to PNG helper
  const convertSvgToPng = async (svgData: string, filename: string) => {
    return new Promise<void>((resolve, reject) => {
      const img = new Image();
      const svg = new Blob([svgData], { type: "image/svg+xml" });
      const url = URL.createObjectURL(svg);

      img.onload = () => {
        const canvas = document.createElement("canvas");
        canvas.width = img.width;
        canvas.height = img.height;
        const context = canvas.getContext("2d");

        if (context) {
          context.drawImage(img, 0, 0);
          canvas.toBlob((blob) => {
            if (blob) {
              const pngUrl = URL.createObjectURL(blob);
              const link = document.createElement("a");
              link.href = pngUrl;
              link.download = filename;
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
              URL.revokeObjectURL(pngUrl);
              resolve();
            } else {
              reject(new Error("Failed to convert to PNG"));
            }
          }, "image/png");
        } else {
          reject(new Error("Failed to get canvas context"));
        }

        URL.revokeObjectURL(url);
      };

      img.onerror = () => {
        URL.revokeObjectURL(url);
        reject(new Error("Failed to load SVG"));
      };

      img.src = url;
    });
  };

  // Extract available types from data
  useEffect(() => {
    if (paperData?.components) {
      const types = new Set(paperData.components.map((comp) => comp.type));
      setAvailableComponentTypes(Array.from(types));
    }

    if (paperData?.relationships) {
      const types = new Set(paperData.relationships.map((rel) => rel.type));
      setAvailableRelationshipTypes(Array.from(types));
    }
  }, [paperData]);

  // Handle settings change
  const handleSettingChange = (
    setting: keyof VisualizationSettings,
    value: unknown
  ) => {
    setSettings((prev) => ({
      ...prev,
      [setting]: value,
    }));
  };

  // Toggle component type filter
  const toggleComponentTypeFilter = (type: string) => {
    setSettings((prev) => {
      const filters = [...prev.componentTypeFilters];
      if (filters.includes(type)) {
        return {
          ...prev,
          componentTypeFilters: filters.filter((t) => t !== type),
        };
      } else {
        return {
          ...prev,
          componentTypeFilters: [...filters, type],
        };
      }
    });
  };

  // Filter components based on settings
  const getFilteredD3Data = (): D3Data | null => {
    if (!d3Data) return null;

    let filteredNodes = [...d3Data.nodes];
    let filteredLinks = [...d3Data.links];

    // Apply component type filters
    if (settings.componentTypeFilters.length > 0) {
      filteredNodes = filteredNodes.filter(
        (node) => !settings.componentTypeFilters.includes(node.type)
      );

      // Also filter links that reference filtered nodes
      const nodeIds = new Set(filteredNodes.map((node) => node.id));
      filteredLinks = filteredLinks.filter(
        (link) =>
          nodeIds.has(link.source.toString()) &&
          nodeIds.has(link.target.toString())
      );
    }

    // Apply relationship type filters
    if (settings.relationshipTypeFilters.length > 0) {
      filteredLinks = filteredLinks.filter(
        (link) => !settings.relationshipTypeFilters.includes(link.type)
      );
    }

    // Filter hierarchical nodes
    let filteredHierarchicalNodes = d3Data.hierarchical_nodes;
    if (filteredHierarchicalNodes && settings.componentTypeFilters.length > 0) {
      // This is a recursive function to filter hierarchical nodes
      const filterChildren = (nodes: ComponentData[]): ComponentData[] => {
        return nodes.filter((node) => {
          // Keep node if its type is not filtered
          const keepNode = !settings.componentTypeFilters.includes(node.type);

          // If node has children, filter them too
          if (keepNode && node.children && node.children.length > 0) {
            node.children = filterChildren(node.children);
          }

          return keepNode;
        });
      };

      // Apply filtering to top-level hierarchical nodes
      filteredHierarchicalNodes = filterChildren(filteredHierarchicalNodes);
    }

    return {
      nodes: filteredNodes,
      links: filteredLinks,
      hierarchical_nodes: filteredHierarchicalNodes,
    };
  };

  // Render visualization based on selected type
  const renderVisualization = () => {
    const isProcessing = paperData?.status === "processing";
    const filteredD3Data = getFilteredD3Data();

    if (visualizationType === "d3" && filteredD3Data) {
      return (
        <D3Visualization
          nodes={filteredD3Data.hierarchical_nodes || filteredD3Data.nodes}
          links={filteredD3Data.links}
          onNodeClick={handleNodeClick}
          isProcessing={isProcessing}
          height={600}
          showMetrics={settings.showMetrics}
          highlightNovel={settings.highlightNovel}
        />
      );
    } else if (visualizationType === "mermaid" && mermaidChart) {
      return (
        <MermaidDiagram chart={mermaidChart} onNodeClick={handleNodeClick} />
      );
    } else {
      // Fallback to simple visualization
      return (
        <SimpleVisualization
          components={paperData?.components || []}
          relationships={paperData?.relationships || []}
          onNodeClick={handleNodeClick}
          isProcessing={isProcessing}
        />
      );
    }
  };

  // Render settings panel
  const renderSettingsPanel = () => {
    return (
      <div
        className="fixed inset-0 z-50 overflow-hidden"
        onClick={() => setSettingsOpen(false)}
      >
        <div
          className="fixed inset-y-0 right-0 max-w-xs w-full bg-white shadow-xl p-6 overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium">Visualization Settings</h3>
            <button
              className="text-gray-400 hover:text-gray-500"
              onClick={() => setSettingsOpen(false)}
            >
              <span className="sr-only">Close</span>
              <svg
                className="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          <div className="space-y-6">
            <div>
              <h4 className="font-medium mb-2">Display Options</h4>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={settings.showNodeLabels}
                    onChange={(e) =>
                      handleSettingChange("showNodeLabels", e.target.checked)
                    }
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="ml-2 text-sm">Show Node Labels</span>
                </label>

                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={settings.showMetrics}
                    onChange={(e) =>
                      handleSettingChange("showMetrics", e.target.checked)
                    }
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="ml-2 text-sm">Show Performance Metrics</span>
                </label>

                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={settings.highlightNovel}
                    onChange={(e) =>
                      handleSettingChange("highlightNovel", e.target.checked)
                    }
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="ml-2 text-sm">
                    Highlight Novel Components
                  </span>
                </label>
              </div>
            </div>

            {availableComponentTypes.length > 0 && (
              <div>
                <h4 className="font-medium mb-2">Filter Component Types</h4>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {availableComponentTypes.map((type) => (
                    <label key={type} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={!settings.componentTypeFilters.includes(type)}
                        onChange={() => toggleComponentTypeFilter(type)}
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                      <span className="ml-2 text-sm capitalize">
                        {type.replace(/_/g, " ")}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {availableRelationshipTypes.length > 0 && (
              <div>
                <h4 className="font-medium mb-2">Filter Relationship Types</h4>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {availableRelationshipTypes.map((type) => (
                    <label key={type} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={
                          !settings.relationshipTypeFilters.includes(type)
                        }
                        onChange={() => {
                          setSettings((prev) => {
                            const filters = [...prev.relationshipTypeFilters];
                            if (filters.includes(type)) {
                              return {
                                ...prev,
                                relationshipTypeFilters: filters.filter(
                                  (t) => t !== type
                                ),
                              };
                            } else {
                              return {
                                ...prev,
                                relationshipTypeFilters: [...filters, type],
                              };
                            }
                          });
                        }}
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                      <span className="ml-2 text-sm capitalize">
                        {type.replace(/_/g, " ")}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            <div className="pt-4 border-t">
              <button
                className="w-full py-2 px-4 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                onClick={() => setSettingsOpen(false)}
              >
                Apply Settings
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Render diagnostic information if available
  const renderDiagnostics = () => {
    if (!paperData?.diagnostics) return null;

    const { diagnostics } = paperData;

    return (
      <div className="mt-4">
        <Card className="overflow-hidden">
          <div className="p-4 border-b bg-gray-50">
            <h3 className="font-medium">Processing Diagnostics</h3>
          </div>
          <div className="p-4 overflow-auto">
            <div className="space-y-4">
              {diagnostics.file_info && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    File Information
                  </h4>
                  <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                    {Object.entries(diagnostics.file_info).map(
                      ([key, value]) => (
                        <React.Fragment key={key}>
                          <dt className="text-gray-500">
                            {key.replace(/_/g, " ")}
                          </dt>
                          <dd className="text-gray-900">
                            {typeof value === "number"
                              ? Math.round(value * 100) / 100
                              : value}
                          </dd>
                        </React.Fragment>
                      )
                    )}
                  </dl>
                </div>
              )}

              {diagnostics.extraction_stages && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    Extraction Stages
                  </h4>
                  <div className="space-y-3">
                    {Object.entries(diagnostics.extraction_stages).map(
                      ([stageKey, stageData]: [string, DiagnosticsStage]) => (
                        <div key={stageKey} className="bg-gray-50 p-3 rounded">
                          <h5 className="font-medium capitalize">
                            {stageKey.replace(/_/g, " ")}
                          </h5>
                          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm mt-2">
                            <dt className="text-gray-500">Status:</dt>
                            <dd className="text-gray-900">
                              <span
                                className={
                                  stageData.status === "success"
                                    ? "text-green-600"
                                    : "text-red-600"
                                }
                              >
                                {stageData.status}
                              </span>
                              {stageData.error && (
                                <span className="text-red-500 text-sm">
                                  {" "}
                                  - Error: {stageData.error}
                                </span>
                              )}
                            </dd>
                          </dl>
                        </div>
                      )
                    )}
                  </div>
                </div>
              )}

              {diagnostics.timings && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    Processing Time (seconds)
                  </h4>
                  <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                    {Object.entries(diagnostics.timings).map(([key, value]) => (
                      <React.Fragment key={key}>
                        <dt className="text-gray-500 capitalize">
                          {key.replace(/_/g, " ")}
                        </dt>
                        <dd className="text-gray-900">
                          {Math.round(value * 100) / 100}s
                        </dd>
                      </React.Fragment>
                    ))}
                  </dl>
                </div>
              )}
            </div>
          </div>
        </Card>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleBack}
              leftIcon={<ArrowLeftIcon />}
            >
              Back
            </Button>
            {paperData?.title || "Paper Visualization"}
          </h1>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              onClick={() => setSettingsOpen(true)}
              title="Visualization Settings"
              leftIcon={<CogIcon />}
            >
              Settings
            </Button>
            <div className="relative">
              <Button
                variant="outline"
                onClick={() => setExportMenuOpen(!exportMenuOpen)}
                title="Export visualization"
                leftIcon={<DownloadIcon />}
              >
                Export
              </Button>

              {exportMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10">
                  <div className="py-1">
                    <button
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      onClick={() => handleExport("svg")}
                    >
                      Export as SVG
                    </button>
                    <button
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      onClick={() => handleExport("png")}
                    >
                      Export as PNG
                    </button>
                    <button
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      onClick={() => handleExport("json")}
                    >
                      Export Data as JSON
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {error ? (
          <div className="space-y-6">
            <Card>
              <div className="p-6">
                <div className="flex items-center mb-4">
                  <div className="bg-red-100 p-2 rounded-full">
                    <svg
                      className="h-6 w-6 text-red-600"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <h3 className="ml-3 text-lg font-medium text-red-800">
                    Processing Error
                  </h3>
                </div>
                <div className="text-red-700 mb-4">{error}</div>
                <div className="mb-4 text-gray-600">
                  This could be due to:
                  <ul className="list-disc pl-5 mt-2 space-y-1">
                    <li>The paper not having a clear ML workflow</li>
                    <li>Poor PDF quality or extraction issues</li>
                    <li>Unsupported paper structure or format</li>
                  </ul>
                </div>
                <div className="flex space-x-4">
                  <Button onClick={handleRetry}>Retry Processing</Button>
                  <Button variant="outline" onClick={handleBack}>
                    Go Back to Upload
                  </Button>
                </div>
              </div>
            </Card>

            {/* Render diagnostic information */}
            {paperData?.diagnostics && renderDiagnostics()}

            {/* Render minimal visualization if components exist despite error */}
            {paperData?.components && paperData.components.length > 0 && (
              <div className="mt-6">
                <Card>
                  <div className="p-4 border-b bg-gray-50">
                    <h3 className="font-medium">
                      Limited Visualization (Based on Partial Extraction)
                    </h3>
                  </div>
                  <div className="p-4 h-[400px]">
                    <SimpleVisualization
                      components={paperData.components || []}
                      relationships={paperData.relationships || []}
                      onNodeClick={handleNodeClick}
                      isProcessing={false}
                    />
                  </div>
                </Card>
              </div>
            )}
          </div>
        ) : loading ? (
          <div className="flex justify-center items-center h-64">
            <Spinner size="lg" />
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <Card className="overflow-hidden">
                <div className="p-4 border-b bg-gray-50 flex justify-between items-center">
                  <h3 className="font-medium">ML Workflow Visualization</h3>
                  <div className="flex items-center space-x-2">
                    <label className="text-sm text-gray-600">View:</label>
                    <select
                      value={visualizationType}
                      onChange={(e) => setVisualizationType(e.target.value)}
                      className="text-sm border rounded px-2 py-1"
                    >
                      <option value="d3">Interactive Graph</option>
                      <option value="mermaid">Flow Diagram</option>
                      <option value="simple">Simple View</option>
                    </select>
                  </div>
                </div>
                <div className="p-4 h-[600px]" ref={visualizationRef}>
                  {renderVisualization()}
                </div>
              </Card>
            </div>

            <div>
              <Tabs
                activeTab={activeTab}
                onChange={setActiveTab}
                tabs={[
                  { id: "details", label: "Component Details" },
                  { id: "stats", label: "Paper Stats" },
                ]}
              />

              <div className="mt-4 h-[600px]">
                {activeTab === "details" ? (
                  <ComponentDetail component={selectedComponent} />
                ) : (
                  <Card>
                    <div className="p-4 h-full overflow-auto">
                      <h3 className="font-medium mb-4">Paper Statistics</h3>
                      <div className="space-y-4">
                        <div>
                          <h4 className="text-sm font-medium text-gray-700">
                            Components:
                          </h4>
                          <p className="text-2xl font-bold">
                            {paperData?.components?.length || 0}
                          </p>
                        </div>
                        <div>
                          <h4 className="text-sm font-medium text-gray-700">
                            Relationships:
                          </h4>
                          <p className="text-2xl font-bold">
                            {paperData?.relationships?.length || 0}
                          </p>
                        </div>
                        {paperData?.paper_type && (
                          <div>
                            <h4 className="text-sm font-medium text-gray-700">
                              Paper Type:
                            </h4>
                            <p className="text-md">{paperData.paper_type}</p>
                          </div>
                        )}

                        {paperData?.diagnostics?.timings?.total && (
                          <div>
                            <h4 className="text-sm font-medium text-gray-700">
                              Processing Time:
                            </h4>
                            <p className="text-md">
                              {Math.round(
                                paperData.diagnostics.timings.total * 10
                              ) / 10}{" "}
                              seconds
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </Card>
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      {settingsOpen && renderSettingsPanel()}
    </div>
  );
}
