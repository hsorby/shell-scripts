import copy
import json
import os

DIR_1 = '/Users/hsor001/Projects/musculoskeletal/workflows/sparc/data/argon_viewer_out'
DIR_2 = '/Users/hsor001/Projects/musculoskeletal/data/vickie_shim_6f1/'

VERSION_INFO = {
    "OpenCMISS-Argon Version": [
        "0",
        "2",
        "2"
    ],
}

SCENE_GRAPHICS = {
    "Scene": {
        "Graphics": [
            {
                "BoundaryMode": "ALL",
                "CoordinateField": "coordinates",
                "ElementFaceType": "ALL",
                "FieldDomainType": "MESH2D",
                "Material": "black",
                "RenderLineWidth": 1,
                "RenderPointSize": 1,
                "RenderPolygonMode": "SHADED",
                "Scenecoordinatesystem": "LOCAL",
                "SelectMode": "ON",
                "SelectedMaterial": "default_selected",
                "Surfaces": {},
                "Tessellation": "default",
                "Type": "SURFACES",
                "VisibilityFlag": True
            }
        ],
        "VisibilityFlag": True
    }
}

FIELD_MODULE = {
    "Fieldmodule": {
        "Fields": [
            {
                "CoordinateSystemType": "RECTANGULAR_CARTESIAN",
                "FieldFiniteElement": {
                    "ComponentNames": [
                        "x",
                        "y",
                        "z"
                    ],
                    "NumberOfComponents": 3
                },
                "IsManaged": True,
                "IsTypeCoordinate": True,
                "Name": "coordinates"
            },
            {
                "CoordinateSystemType": "FIBRE",
                "FieldFiniteElement": {
                    "ComponentNames": [
                        "fibre angle",
                        "imbrication angle",
                        "sheet angle"
                    ],
                    "NumberOfComponents": 3
                },
                "IsManaged": True,
                "IsTypeCoordinate": False,
                "Name": "fibres"
            }
        ]
    },
}

EMPTY_REGION = {
    "Fieldmodule": None,
    "Scene": {
        "Graphics": None,
        "VisibilityFlag": True
    }
}

SKIP_REGIONS = ['maxilla', ]


def main():
    os.walk(DIR_2)
    data_files = []
    for root, dirs, files in os.walk(DIR_2, topdown=True):
        current_dir = {
            'node_files': [],
            'elem_files': []
        }
        for file in files:
            # print(file)
            if file.endswith('.EXNODE'):
                current_dir['node_files'].append(os.path.join(root, file))
            if file.endswith('.EXELEM'):
                current_dir['elem_files'].append(os.path.join(root, file))

        if len(current_dir["node_files"]):
            data_files.append(current_dir)

    common_path = os.path.commonpath([d["node_files"][0] for d in data_files])

    argon_document = {
        **VERSION_INFO
    }

    root_region = copy.deepcopy(EMPTY_REGION)

    bits = []
    for index, data in enumerate(data_files):

        exnode_file = data["node_files"][0]
        region_path = exnode_file.replace(common_path, '')

        region_parts = region_path.split('/')
        region_parts.pop(0)
        base_region = root_region
        for i in range(len(region_parts) - 1):
            current_region = region_parts[i].lower()

            if "ChildRegions" not in base_region:
                base_region["ChildRegions"] = []

            child_region_names = []
            for region_info in base_region["ChildRegions"]:
                child_region_names.append(region_info["Name"])

            if current_region not in child_region_names:
                new_child = copy.deepcopy(EMPTY_REGION)
                new_child['Name'] = current_region
                base_region["ChildRegions"].append(new_child)
                child_region_names.append(current_region)

            j = child_region_names.index(current_region)

            base_region = base_region["ChildRegions"][j]

        # base_region["Fieldmodule"] = copy.deepcopy(FIELD_MODULE["Fieldmodule"])
        base_region["Scene"] = copy.deepcopy(SCENE_GRAPHICS["Scene"])
        bit = f"'{region_parts[-2].lower()}',"
        # if bit not in bits:
        #     bits.append(bit)
        if region_parts[-2].lower() in SKIP_REGIONS:
            continue

        if "Model" not in base_region:
            base_region["Model"] = {"Sources": []}

        for node_file in data['node_files']:
            exnode_path = node_file  # .replace(common_path, '')[1:]
            base_region["Model"]["Sources"].insert(
                0,
                {
                    "FileName": exnode_path,
                    "RegionName": os.path.dirname(region_path).lower(),
                    "Type": "FILE"
                }
            )
        for elem_file in data['elem_files']:
            exelem_path = elem_file  # .replace(common_path, '')[1:]
            base_region["Model"]["Sources"].append(
                {
                    "FileName": exelem_path,
                    "RegionName": os.path.dirname(region_path).lower(),
                    "Type": "FILE"
                }
            )

        if 'MUSCLES' in region_path or 'NECK' in region_path:
            base_region["Scene"]["Graphics"][0]["Material"] = "muscle"
        if 'BONE' in region_path:
            base_region["Scene"]["Graphics"][0]["Material"] = "bone"
        if 'LIGAMENT' in region_path:
            base_region["Scene"]["Graphics"][0]["Material"] = "white"
        if 'SKIN' in region_path:
            base_region["Scene"]["Graphics"][0]["Material"] = "brown"

    argon_document["RootRegion"] = root_region

    print('\n'.join(bits))
    with open(os.path.join(DIR_2, 'test_file.json'), 'w') as f:
        f.write(json.dumps(argon_document, default=lambda o: o.__dict__, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()

model_sources = {
    "Model": {
        "Sources": [
            {
                "FileName": "FEMUR.EXNODE",
                "RegionName": "/left_lower_limb/bones/femur",
                "Type": "FILE"
            },
            {
                "FileName": "FEMUR.EXELEM",
                "RegionName": "/left_lower_limb/bones/femur",
                "Type": "FILE"
            }
        ]
    },
}
