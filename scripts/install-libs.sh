#!/usr/bin/env bash

set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
vendor_dir="$root_dir/public/vendor"

download() {
	local url="$1"
	local destination="$2"
	local destination_dir
	destination_dir="$(dirname "$destination")"
	mkdir -p "$destination_dir"
	local temp_file
	temp_file="${destination}.tmp"
	trap 'rm -f "$temp_file"' RETURN
	curl -fsSL "$url" -o "$temp_file"
	mv "$temp_file" "$destination"
	trap - RETURN
}

mkdir -p "$vendor_dir/bootstrap"

download "https://cdn.jsdelivr.net/npm/cytoscape@3.16.2/dist/cytoscape.min.js" "$vendor_dir/cytoscape.min.js"
download "https://cdn.jsdelivr.net/npm/cytoscape-dagre@4.0.0/dist/cytoscape-dagre.min.js" "$vendor_dir/cytoscape-dagre.min.js"
download "https://cdn.jsdelivr.net/npm/dagre@0.7.4/dist/dagre.min.js" "$vendor_dir/dagre.min.js"
download "https://cdn.jsdelivr.net/npm/plotly.js-dist-min@3.1.2/plotly.min.js" "$vendor_dir/plotly.min.js"
download "https://cdn.jsdelivr.net/npm/bootstrap@4.1.3/dist/css/bootstrap.min.css" "$vendor_dir/bootstrap/bootstrap.css"