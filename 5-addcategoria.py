#!/usr/bin/env python
"""
Add category to a socio (member).

This script adds a specified category to a socio using the API.
Usage: python 5-addcategoria.py <idCategoria> <idColegiat>
"""

import sys

import common


def main() -> None:
    """Main function to add category to socio."""
    # Setup logging
    logger = common.setup_script_logging("addcategoria")

    # Parse arguments
    try:
        id_categoria, id_colegiat = common.parse_two_int_args(
            "addcategoria.py", "idCategoria", "idColegiat"
        )
    except SystemExit:
        return

    logger.info(f"Processing Category: {id_categoria} for Socio: {id_colegiat}")

    try:
        # Get authentication token
        token = common.get_rw_token()

        # Add category to socio
        response = common.addcategoria(
            token=token, socio=id_colegiat, categoria=id_categoria
        )

        # Handle response
        common.handle_api_error(
            response, f"adding category {id_categoria} to socio {id_colegiat}"
        )

        if response.status_code < 400:
            print(f"Successfully added category {id_categoria} to socio {id_colegiat}")
            if response.text:
                print(f"API Response: {response.text}")

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        print(f"Error: Failed to add category. {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
