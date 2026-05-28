import pandas as pd
import streamlit as st

from ui.utils import load_dataset_mappings, data_type_from_filename, plot_dataset_chart, highlight_turtle_clinical
from src.exporters import load_sync_state, export_to_solid, export_combined, update_sync_state_for_dtype, graph_to_turtle_string
from src.rdf_transformer import transform_export, load_template, count_clinical_triples, graph_to_jsonld, merge_graphs, TransformOptions

def render_vault_admin(dark_mode: bool, normalized: dict, export_path: str, template_path: str, output_path: str):
    if "transform_options" not in st.session_state:
        st.session_state.transform_options = TransformOptions(
            clinical_mode=True,
            include_provenance=True
        )
    transform_options = st.session_state.transform_options

    st.divider()
    st.markdown("## ⚙️ Settings & Vault Administration")
    
    tab_data, tab_ontology, tab_rdf, tab_preview, tab_solid, tab_future = st.tabs([
        "Data Overview",
        "Ontology Settings",
        "RDF Transform",
        "RDF Preview",
        "Solid Export",
        "Future Sources",
    ])

    with tab_data:
        mappings = load_dataset_mappings()
        
        st.markdown("## 🔍 Samsung Health Data Explorer")
        st.write("Browse and inspect all datasets extracted from the Samsung Health export. Select any dataset to view details, render custom plots, or view the raw database table.")
        
        st.divider()
        
        c_left, c_right = st.columns([1, 2])
        
        with c_left:
            st.markdown("### 📁 Dataset Catalog")
            search_query = st.text_input("Search datasets...", placeholder="e.g. weight, sleep...", key="explorer_search")
            
            categories = ["All", "Activity", "Sleep", "Nutrition", "Cardiovascular", "Body / Profile", "System", "Other"]
            selected_category = st.selectbox("Filter by Category", categories, key="explorer_category")
            
            dataframes = normalized.get("dataframes", {})
            filtered_datasets = []
            
            for fname, df in dataframes.items():
                dtype = data_type_from_filename(fname)
                mapping = mappings.get(dtype, {})
                
                display_name = mapping.get("display_name", dtype)
                icon = mapping.get("icon", "📄")
                category = mapping.get("category", "Other")
                description = mapping.get("description", "No description available.")
                
                if selected_category != "All" and category != selected_category:
                    continue
                if search_query and search_query.lower() not in display_name.lower() and search_query.lower() not in dtype.lower():
                    continue
                    
                filtered_datasets.append({
                    "filename": fname,
                    "dtype": dtype,
                    "display_name": display_name,
                    "icon": icon,
                    "category": category,
                    "description": description,
                    "rows": len(df),
                    "df": df
                })
                
            filtered_datasets = sorted(filtered_datasets, key=lambda x: x["display_name"])
            
            if not filtered_datasets:
                st.info("No datasets match your filters.")
                selected_ds = None
            else:
                options = [f"{d['icon']} {d['display_name']} ({d['rows']:,} rows)" for d in filtered_datasets]
                selected_index = st.selectbox("Select a Dataset to View", range(len(options)), format_func=lambda i: options[i], key="explorer_select")
                selected_ds = filtered_datasets[selected_index]
                
        with c_right:
            if selected_ds:
                st.markdown(f"### {selected_ds['icon']} {selected_ds['display_name']}")
                st.caption(f"**Category:** {selected_ds['category']} | **Filename:** `{selected_ds['filename']}`")
                st.write(selected_ds['description'])
                
                df = selected_ds['df']
                dtype = selected_ds['dtype']
                
                st.markdown("#### 📈 Visualization")
                plot_dataset_chart(dtype, df, selected_ds['display_name'])
                
                st.divider()
                
                with st.expander("🛠️ Advanced Raw Data View", expanded=False):
                    st.markdown("#### Columns and Data Types")
                    cols_info = pd.DataFrame({
                        "Data Type": [str(df[col].dtype) for col in df.columns],
                        "Non-Null Count": [df[col].notna().sum() for col in df.columns],
                        "Null Count": [df[col].isna().sum() for col in df.columns]
                    }, index=df.columns)
                    st.dataframe(cols_info, use_container_width=True)
                    
                    st.markdown("#### Data Sample")
                    st.dataframe(df, use_container_width=True, height=300)
                    
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download CSV dataset",
                        data=csv_data,
                        file_name=selected_ds['filename'],
                        mime='text/csv',
                        key=f"dl_{dtype}"
                    )
            else:
                st.info("Select a dataset from the catalog on the left to view charts and raw data.")

        st.divider()
        st.markdown("### 📋 Complete Dataset Overview & RDF Sync Tracker")
        st.write("A comprehensive list of all supported datasets, their load status, and actionable RDF synchronization controls.")
        
        try:
            tmpl = load_template(template_path)
            mapped_types = set(tmpl.mappings.keys())
        except Exception:
            mapped_types = set()
            
        sync_state = load_sync_state(output_path)
        loaded_fnames = {data_type_from_filename(f): f for f in normalized.get("dataframes", {}).keys()}
        
        h1, h2, h3, h4, h5 = st.columns([3, 2, 2, 2, 2])
        h1.markdown("**Dataset**")
        h2.markdown("**Loaded**")
        h3.markdown("**RDF Mapping**")
        h4.markdown("**Sync Status**")
        h5.markdown("**Action**")
        st.markdown("<hr style='margin: 0px;'/>", unsafe_allow_html=True)
        
        for dtype, mapping in mappings.items():
            is_loaded = dtype in loaded_fnames
            is_mapped = dtype in mapped_types
            
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])
            c1.write(f"{mapping.get('icon', '📄')} {mapping.get('display_name', dtype)}")
            c2.write("✅ Yes" if is_loaded else "❌ No")
            c3.write("Complete" if is_mapped else "No")
            
            if is_loaded and is_mapped:
                fname = loaded_fnames[dtype]
                df = normalized["dataframes"][fname]
                current_rows = len(df)
                state_info = sync_state.get(dtype)
                
                if not state_info:
                    status = "Not Imported ❌"
                    btn_label = "Import to RDF"
                else:
                    synced_rows = state_info.get("row_count", 0)
                    if current_rows > synced_rows:
                        status = "Incomplete ⚠️"
                        btn_label = "Update RDF"
                    else:
                        status = "Up to Date ✅"
                        btn_label = "Re-Import"
                        
                c4.write(status)
                
                if c5.button(btn_label, key=f"sync_{dtype}"):
                    with st.spinner(f"Converting {dtype}..."):
                        scoped_norm = {"dataframes": {fname: df}}
                        try:
                            single_graph = transform_export(scoped_norm, template_path, progress=False, options=transform_options)
                            if single_graph:
                                export_to_solid(single_graph, output_path)
                                update_sync_state_for_dtype(output_path, dtype, current_rows)
                                st.rerun()
                        except Exception as e:
                            st.error(f"Failed to sync {dtype}: {e}")
            else:
                c4.write("-")
                c5.write("-")
                
            st.markdown("<hr style='margin: 0.5em 0px;'/>", unsafe_allow_html=True)

    with tab_ontology:
        st.markdown("## 🏷️ Ontology Mappings & Configurations")
        st.write("Configure the RDF ontology mapping mode, provenance tracking, and view active template namespaces.")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### ⚙️ Mapping Rules")
            
            curr_mode = "clinical" if st.session_state.transform_options.clinical_mode else "simple"
            curr_prov = st.session_state.transform_options.include_provenance
            
            mode = st.radio(
                "Mapping Mode",
                options=["simple", "clinical"],
                index=1 if curr_mode == "clinical" else 0,
                format_func=lambda x: (
                    "Simple (schema.org + QUDT + PROV)"
                    if x == "simple"
                    else "Clinical (+ SNOMED / LOINC / FHIR links)"
                ),
                help="Clinical mode adds interoperability reference triples; no full ontology import.",
                key="opt_mapping_mode"
            )
            
            include_prov = st.checkbox(
                "Include PROV-O Provenance",
                value=curr_prov,
                help="Appends Samsung export metadata and tracking records using PROV-O.",
                key="opt_include_prov"
            )
            
            st.session_state.transform_options = TransformOptions(
                clinical_mode=(mode == "clinical"),
                include_provenance=include_prov
            )
            transform_options = st.session_state.transform_options
            
        with col2:
            try:
                tmpl = load_template(template_path)
                st.markdown("### 🌐 Template Namespaces")
                for prefix, uri in tmpl.namespaces.items():
                    st.caption(f"`{prefix}` → {uri[:48]}…" if len(uri) > 48 else f"`{prefix}` → {uri}")
                    
                st.markdown("### 🏷️ Active Semantic Mappings")
                with st.expander("Show Mapped Samsung Fields", expanded=False):
                    st.code("\n".join(tmpl.mappings.keys()), language=None)
            except Exception as e:
                st.warning(f"Failed to inspect template: {e}")

    graphs = None
    with tab_rdf:
        st.subheader("Apply ontology template")
        mode_label = "clinical" if transform_options.clinical_mode else "simple"
        st.info(f"Active mode: **{mode_label}**")

        if st.button("Apply Template & Generate RDF", type="primary"):
            with st.spinner("Generating RDF…"):
                graphs = transform_export(
                    normalized,
                    template_path,
                    progress=True,
                    options=transform_options,
                )
            st.session_state["graphs"] = graphs
            st.session_state["clinical_mode"] = transform_options.clinical_mode
            total = sum(len(g) for g in graphs.values())
            st.success(f"Generated {len(graphs)} graphs, {total} triples total")

    clinical_active = transform_options.clinical_mode
    if "graphs" in st.session_state:
        graphs = st.session_state["graphs"]
        clinical_active = st.session_state.get("clinical_mode", clinical_active)
    else:
        from ui.utils import cached_transform
        try:
            graphs = cached_transform(
                export_path, template_path, transform_options.clinical_mode, output_path=output_path
            )
        except Exception:
            graphs = {}

    with tab_preview:
        st.subheader("RDF preview")
        if not graphs:
            st.info("Generate RDF first (RDF Transform tab).")
        else:
            dtype = st.selectbox("Data type", list(graphs.keys()))
            g = graphs[dtype]
            counts = count_clinical_triples(g)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("QUDT-related", counts["qudt"])
            c2.metric("SNOMED", counts["snomed"])
            c3.metric("LOINC", counts["loinc"])
            c4.metric("FHIR", counts["fhir"])

            fmt = st.radio("Format", ["Turtle", "JSON-LD"], horizontal=True)
            if fmt == "Turtle":
                turtle = graph_to_turtle_string(g)
                if clinical_active:
                    st.markdown("**Clinical / QUDT highlights**")
                    st.markdown(highlight_turtle_clinical(turtle), unsafe_allow_html=True)
                else:
                    st.code(turtle, language="turtle")
            else:
                st.code(graph_to_jsonld(g), language="json")

            merged = merge_graphs(graphs)
            st.download_button(
                "Download combined Turtle",
                merged.serialize(format="turtle"),
                file_name="health_combined.ttl",
                mime="text/turtle",
            )
            st.download_button(
                "Download combined JSON-LD",
                graph_to_jsonld(merged),
                file_name="health_combined.jsonld",
                mime="application/ld+json",
            )

    with tab_solid:
        st.subheader("Solid pod-style export")
        if not graphs:
            st.warning("No RDF graphs available. Run transformation first.")
        elif st.button("Write Solid folder structure", type="primary"):
            paths = export_to_solid(graphs, output_path, also_jsonld=True)
            combined = export_combined(graphs, output_path)
            st.success(f"Exported to `{output_path}`")
            st.write("Turtle:", [str(p) for p in paths["ttl"]])
            st.write("JSON-LD:", [str(p) for p in paths["jsonld"]])
            st.write("Combined:", str(combined))

    with tab_future:
        st.subheader("Extensibility")
        st.markdown(
            """
            **Ontology stack**

            | Layer | Use |
            |-------|-----|
            | schema.org | Primary consumer health types |
            | QUDT | Units (kg, BPM, minutes) |
            | PROV-O | Samsung export provenance |
            | health: | Samsung-specific fields |
            | SNOMED / LOINC / FHIR | Optional links (clinical mode) |

            **Planned loaders** (same pipeline, new `mappings:` blocks):

            - Pathology PDF → `fhir:Observation` + LOINC codes
            - Google Timeline → `schema:Place` + environmental sensors
            """
        )
