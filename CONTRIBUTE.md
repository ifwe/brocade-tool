# Contribute

## Coding Style
* PEP8

## Adding/Changing features
* Please send your changes as a pull request

### Add a new top level argument, i.e. show
1. Creating a new parser off of the main subparser
    * ```
    parser_show = subparser.add_parser(
        'show', help='sub-command for showing objects'
    )
    ```

### Add a new second level argument, i.e. lb-vservers
1. Create a new subparser off of parent subparser
    * `subparser_show = parser_show.add_subparsers(dest='subparser_name')`
1. Create parser

        subparser_show = parser_show.add_subparsers(dest="subparser_name")

    * If the subparser will need an argument
        -
        
            parser_show_ports = subparser_show.add_parser("ports",
                help="sub-command for showing stats about all ports"
            )

1. Create new method under respective class
    *   
        
        class Show(object):
            def __init__(self):
                ...
                
            def ports(self):
                ...
