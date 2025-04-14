return (
  <div className="w-full h-full overflow-auto p-4">
    {component ? (
      <>
        <h2 className="text-xl font-bold mb-4">{component.name}</h2>
        {component.description && (
          <div className="mb-4">
            <p className="whitespace-pre-wrap">{component.description}</p>
          </div>
        )}
        {/* Keep all other elements like relations, metadata, etc. */}
        {/* ... existing code ... */}
      </>
    ) : (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-500">Select a component to view details</p>
      </div>
    )}
  </div>
);
