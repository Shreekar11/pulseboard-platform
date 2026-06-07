/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type ReadyzResponse = {
    status: string;
    checks: {
        redis?: boolean;
        postgres?: boolean;
    };
};

