import os
import asyncio

mode = os.getenv('PARSER_MODE', 'sync')

if mode == 'async':
    from src.task2.async_parser import main
    asyncio.run(main())
else:
    from src.task2 import parser
    parser.run()