import type { NextConfig } from "next";
import devupApi from "@devup-api/next-plugin";
import { DevupUI } from "@devup-ui/next-plugin";

const nextConfig: NextConfig = {
  /* config options here */
};

export default DevupUI(devupApi(nextConfig));
