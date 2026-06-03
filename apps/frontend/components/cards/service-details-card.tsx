"use client";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { getInfo } from "@/lib/api";
import { useAsyncFetch } from "@/hooks/use-async-fetch";

export function ServiceDetailsCard() {
  const { data: info, loading, error } = useAsyncFetch(() => getInfo(), []);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-medium">Service details</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-full" />
          </div>
        ) : error ? (
          <p className="text-xs text-destructive">{error}</p>
        ) : !info ? (
          <p className="text-sm text-muted-foreground">
            Service details unavailable.
          </p>
        ) : (
          <dl className="grid grid-cols-2 gap-y-3 text-sm">
            <dt className="text-muted-foreground">Cloud provider</dt>
            <dd className="text-right">
              <Badge variant="secondary">{info.cloud_provider}</Badge>
            </dd>

            <dt className="text-muted-foreground">Region</dt>
            <dd className="text-right font-mono">{info.region}</dd>

            <dt className="text-muted-foreground">Version</dt>
            <dd className="text-right font-mono">{info.version}</dd>

            <dt className="text-muted-foreground">Buffer</dt>
            <dd className="text-right font-mono">{info.buffer}</dd>
          </dl>
        )}
      </CardContent>
    </Card>
  );
}
