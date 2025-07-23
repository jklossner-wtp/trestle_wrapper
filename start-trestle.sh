#!/bin/bash

export TRESTLE_ID=trestle_WhitetailPropertiesRealEstateLLCChatGPTIntegration20250721102610
export TRESTLE_SEC=0b9616628e31415b9d08e872ead0f3cd

uvicorn trestle_app:app --reload --log-level debug

