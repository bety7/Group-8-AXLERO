import great_expectations as gx
import pandas as pd

df = pd.DataFrame({
    "order_id": ["a", "b", "c", "d"],
    "user_id": [1, 2, None, 4],
    "tax_amount": [1.2, None, 3.4, 5.6],
    "total": [10.0, 20.0, 30.0, 40.0],
})

context = gx.get_context()
source = context.data_sources.add_pandas("events")
asset = source.add_dataframe_asset("checkout")
batch_def = asset.add_batch_definition_whole_dataframe("whole")
batch = batch_def.get_batch(batch_parameters={"dataframe": df})

suite = context.suites.add(gx.ExpectationSuite(name="checkout_quality"))
for col in ["order_id", "user_id", "tax_amount", "total"]:
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column=col))

result = batch.validate(suite)
print("Suite passed:", result.success)
for r in result.results:
    print(" ", r.expectation_config.kwargs["column"], "->", r.success)