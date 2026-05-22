#!/usr/bin/env python3
"""Production Python gRPC/Stubby Client for CWP.PricingService."""

import argparse
import json
import os
import sys
from absl import logging
import grpc
from pyglib.stubby.python import stubby

# Google3 pricing stubs imports
from google3.cloud.ux.api.webplatform.pricing import service_pb2
from google3.cloud.ux.api.webplatform.pricing import service_pb2_grpc

# Production BNS endpoint for CWP PricingService
_CWP_PRICING_SERVICE_BNS = "/bns/qd/borg/qd-prd/cwp-pricingservice/0"


class CwpPricingClient:
  """Stubby client to interact with CWP.PricingService for cost estimation."""

  def __init__(self, target_bns: str = _CWP_PRICING_SERVICE_BNS):
    logging.info("Initializing CwpPricingClient with BNS: %s", target_bns)
    # Initialize Stubby channel over BNS inheriting active Cloudtop LOAS credentials
    self._channel = stubby.StubbyChannel(target_bns)
    self._stub = service_pb2_grpc.PricingServiceStub(self._channel)

  def get_sku_pricing(self, product_id: str, region: str = "us-central1") -> dict:
    """Queries GetPricingForm to retrieve detailed SKU price structures."""
    logging.info("Fetching pricing form for product: %s in region: %s", product_id, region)
    request = service_pb2.GetPricingFormRequest(
        product_id=product_id,
        region_code=region
    )
    
    # Pass LOAS credentials policy to ensure enterprise contract pricing is reflected
    metadata = [("af_auth_gaia_loas_creds_policy", "BEST_EFFORT")]
    
    try:
      response = self._stub.GetPricingForm(request, timeout=10.0, metadata=metadata)
      return {
          "product_id": product_id,
          "region": region,
          "form_data": response.pricing_form_data.form_fields,
          "currency": response.pricing_form_data.currency_code,
      }
    except grpc.RpcError as e:
      logging.error("Stubby call failed: %s", e)
      raise RuntimeError(f"Failed to fetch pricing for {product_id}: {e.details()}") from e

  def execute_estimate_stream(self, architecture_payload: dict) -> dict:
    """Executes StreamPricingAgentAction for real-time SKU estimate math."""
    logging.info("Executing streaming estimate calculation.")
    request = service_pb2.StreamPricingAgentActionRequest(
        action_type=service_pb2.StreamPricingAgentActionRequest.ACTION_TYPE_CALCULATE_ESTIMATE,
        payload_json=json.dumps(architecture_payload)
    )
    
    metadata = [("af_auth_gaia_loas_creds_policy", "BEST_EFFORT")]
    
    try:
      response_stream = self._stub.StreamPricingAgentAction(iter([request]), timeout=30.0, metadata=metadata)
      final_estimate = {}
      for response in response_stream:
        if response.HasField("estimate_result_json"):
          final_estimate.update(json.loads(response.estimate_result_json))
      return final_estimate
    except grpc.RpcError as e:
      logging.error("Streaming Stubby call failed: %s", e)
      raise RuntimeError(f"Estimate calculation stream failed: {e.details()}") from e

def main():
    parser = argparse.ArgumentParser(description="Stubby BNS CLI wrapper client for CWP.PricingService.")
    parser.add_argument("--payload_path", required=True, help="Path to local JSON file containing the GCS/GKE/VM infrastructure topology.")
    parser.add_argument("--output_path", required=True, help="Path to save the calculated pricing estimate JSON results.")
    args = parser.parse_args()
    
    if not os.path.exists(args.payload_path):
        print(f"❌ Error: Payload file not found at [{args.payload_path}]", file=sys.stderr)
        sys.exit(1)
        
    try:
        with open(args.payload_path, 'r', encoding='utf-8') as f:
            payload = json.load(f)
            
        client = CwpPricingClient()
        print(f"⚡ Querying CWP.PricingService over BNS for payload...")
        estimate_results = client.execute_estimate_stream(payload)
        
        # Ensure parent directory exists
        parent = os.path.dirname(args.output_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
            
        with open(args.output_path, 'w', encoding='utf-8') as f:
            json.dump(estimate_results, f, indent=2)
            
        print(f"🚀 Success! Estimated pricing saved to: {args.output_path}")
        
    except Exception as e:
        print(f"❌ Execution failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
