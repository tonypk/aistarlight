import { computed } from "vue";
import { useRoute } from "vue-router";

const ROUTE_AGENT_MAP: Record<string, string> = {
  "/reports": "filing",
  "/reconciliation": "recon",
  "/bank-reconciliation": "recon",
  "/classification": "classifier",
  "/journal-entries": "journal",
  "/general-ledger": "journal",
  "/statements": "filing",
  "/tax-bridge": "filing",
  "/calendar": "compliance",
  "/penalty-calculator": "compliance",
  "/form-router": "filing",
  "/chat": "general",
};

export function useRouteAgent() {
  const route = useRoute();

  const suggestedAgent = computed(() => {
    const path = route.path;
    for (const [routePrefix, agentId] of Object.entries(ROUTE_AGENT_MAP)) {
      if (path === routePrefix || path.startsWith(routePrefix + "/")) {
        return agentId;
      }
    }
    return "general";
  });

  return { suggestedAgent };
}
