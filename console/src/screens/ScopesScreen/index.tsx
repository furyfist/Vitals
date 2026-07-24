import { Search } from "lucide-react";
import type React from "react";
import EmptyState from "@/components/EmptyState";
import PageHeader from "@/components/PageHeader";
import Skeleton from "@/components/Skeleton";
import ScopeCard from "@/features/scopes/components/ScopeCard";
import { useScopes } from "@/hooks/useScopes";

export const ScopesScreen: React.FC = () => {
  const { data: scopes = [], isLoading, isError } = useScopes();

  return (
    <div style={{ padding: "32px var(--layout-gutter)", maxWidth: "var(--layout-max)", margin: "0 auto", width: "100%" }}>
      <PageHeader
        title="Scopes"
        subtitle="What Vitals is currently watching."
      />

      {isLoading ? (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))",
            gap: "24px",
          }}
        >
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} variant="block" height={220} />
          ))}
        </div>
      ) : isError ? (
        <div style={{ textAlign: "center", padding: "48px 0" }}>
          <p style={{ color: "var(--color-error-text)" }}>Failed to load scopes from server.</p>
        </div>
      ) : scopes.length === 0 ? (
        <EmptyState
          icon={<Search size={24} aria-hidden="true" />}
          title="No scopes yet"
          body="A scope appears once Vitals sees its first GenAI span."
        />
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))",
            gap: "24px",
          }}
        >
          {scopes.map((scope) => (
            <ScopeCard key={`${scope.service_name}-${scope.model}`} scope={scope} />
          ))}
        </div>
      )}
    </div>
  );
};

export default ScopesScreen;
