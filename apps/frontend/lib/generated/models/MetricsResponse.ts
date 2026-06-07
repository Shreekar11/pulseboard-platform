/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { MetricPoint } from './MetricPoint';
export type MetricsResponse = {
    /**
     * Event type filter applied. 'all' when no type filter was specified (aggregate across all types).
     */
    type: string;
    interval: string;
    from: string;
    to: string;
    series: Array<MetricPoint>;
};

