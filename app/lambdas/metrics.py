from aws_lambda_typing import events, context



def process_metrics(event: events.SQSEvent, ctx: context.Context ):
    records = event.get('Records')

