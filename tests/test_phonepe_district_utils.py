import unittest
import pandas as pd
from phonepe_district_utils import match_districts, choose_boundaries


class DistrictMatchingTests(unittest.TestCase):
    def test_same_state_exact_and_known_alias_only(self):
        geo={'features':[{'properties':{'state':'Karnataka','district':'Bangalore','shape_key':'KA|BLR'}},
                         {'properties':{'state':'Karnataka','district':'Hassan','shape_key':'KA|HAS'}},
                         {'properties':{'state':'Other','district':'Hassan','shape_key':'XX|HAS'}}]}
        frame=pd.DataFrame({'district':['bengaluru urban district','hassan district','unknown district']})
        result,unmatched=match_districts(frame,geo,'karnataka')
        self.assertEqual(result.shape_key.tolist()[:2],['KA|BLR','KA|HAS'])
        self.assertEqual(unmatched,['unknown district'])

    def test_ambiguous_current_names_are_not_mapped_twice(self):
        geo={'features':[{'properties':{'state':'Karnataka','district':'Bangalore','shape_key':'KA|BLR'}}]}
        frame=pd.DataFrame({'district':['bengaluru urban district','bangalore district']})
        result,unmatched=match_districts(frame,geo,'karnataka')
        self.assertEqual(len(unmatched),2)
        self.assertTrue(result.shape_key.isna().all())

    def test_exact_new_name_is_preferred_over_old_alias(self):
        geo={'features':[{'properties':{'state':'Karnataka','district':'Ballari','shape_key':'new'}},
                         {'properties':{'state':'Karnataka','district':'Bellary','shape_key':'old'}}]}
        result,unmatched=match_districts(pd.DataFrame({'district':['ballari district']}),geo,'karnataka')
        self.assertEqual(result.shape_key.tolist(),['new'])
        self.assertEqual(unmatched,[])

    def test_selects_one_collection_with_most_matches(self):
        def feature(d,k): return {'properties':{'state':'Telangana','district':d,'shape_key':k}}
        old={'features':[feature('Hyderabad','a')]}
        new={'features':[feature('Hyderabad','b'),feature('Jagitial','c')]}
        frame=pd.DataFrame({'district':['hyderabad district','jagtial district']})
        label,geo,result,unmatched=choose_boundaries(frame,'telangana',[('old',old),('new',new)])
        self.assertEqual(label,'new')
        self.assertEqual(result.shape_key.tolist(),['b','c'])
        self.assertEqual(unmatched,[])


if __name__ == '__main__': unittest.main()
