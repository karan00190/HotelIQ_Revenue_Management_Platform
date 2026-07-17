import { AssistantPageClient } from "@/components/assistant/AssistantPageClient";
import { assistantApi, hotelsApi } from "@/lib/api";

export default async function AssistantPage() {
  const [status, hotels] = await Promise.all([assistantApi.status(), hotelsApi.list()]);

  return <AssistantPageClient initialStatus={status} hotels={hotels} />;
}
