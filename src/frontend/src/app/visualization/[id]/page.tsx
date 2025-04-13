"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import mermaid from "mermaid";
import { Spinner, Alert, Card, Button } from "@/components/ui"; // Use path alias
import { ArrowLeftIcon } from "@/components/icons"; // Use path alias

// Initialize Mermaid on client side
if (typeof window !== "undefined") {
  mermaid.initialize({
    startOnLoad: false,
    theme: "default", // or 'dark', 'forest', 'neutral'
    securityLevel: "loose", // Required for dynamic rendering
  });
}

interface ExamplePaperDetail {
  id: string;
  title: string;
  description: string;
  mermaid_graph: string;
}

const MermaidDiagram: React.FC<{ chart: string }> = ({ chart }) => {
  const mermaidRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (mermaidRef.current && chart) {
      mermaid
        .render("mermaid-graph-" + Date.now(), chart)
        .then(({ svg, bindFunctions }) => {
          if (mermaidRef.current) {
            mermaidRef.current.innerHTML = svg;
            if (bindFunctions) {
              bindFunctions(mermaidRef.current);
            }
          }
        })
        .catch((err) => {
          console.error("Error rendering Mermaid chart:", err);
          if (mermaidRef.current) {
            mermaidRef.current.innerHTML = "Error rendering diagram.";
          }
        });
    }
    return () => {
      if (mermaidRef.current) {
        mermaidRef.current.innerHTML = ""; // Clean up on unmount or chart change
      }
    };
  }, [chart]);

  return (
    <div
      ref={mermaidRef}
      className="mermaid-container w-full h-full flex justify-center items-center p-4"
    ></div>
  );
};

export default function VisualizationPage(): React.ReactNode {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [paperDetails, setPaperDetails] = useState<ExamplePaperDetail | null>(
    null
  );
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    if (!id) {
      setError("No example ID provided.");
      setLoading(false);
      return;
    }

    const fetchDetails = async () => {
      setLoading(true);
      setError("");
      try {
        const response = await fetch(`/api/examples/${id}`); // Fetch specific example
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error(`Example paper with ID '${id}' not found.`);
          } else {
            throw new Error("Failed to fetch example paper details");
          }
        }
        const data: ExamplePaperDetail = await response.json();
        setPaperDetails(data);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Unknown error fetching details"
        );
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
  }, [id]);

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8">
      <Button
        variant="outline"
        onClick={() => router.back()}
        className="mb-4"
        leftIcon={<ArrowLeftIcon />}
      >
        Back
      </Button>

      {loading && (
        <div className="flex justify-center items-center h-64">
          <Spinner size="lg" />
        </div>
      )}

      {error && (
        <Alert
          type="error"
          message={`Error loading visualization: ${error}`}
          className="mb-4"
        />
      )}

      {paperDetails && !loading && !error && (
        <Card className="overflow-hidden">
          <div className="p-6 border-b">
            <h1 className="text-2xl font-bold text-gray-900">
              {paperDetails.title}
            </h1>
            <p className="mt-1 text-gray-600">{paperDetails.description}</p>
          </div>
          <div className="p-6 bg-white" style={{ minHeight: "60vh" }}>
            <MermaidDiagram chart={paperDetails.mermaid_graph} />
          </div>
        </Card>
      )}
    </div>
  );
}
