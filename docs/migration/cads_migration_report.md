
# CADS Professors Migration Report

## Overview
This report summarizes the CADS professors that will be migrated to the subset tables.

## Total Professors: 55

## Professor List:
 1. Xiangping Liu
 2. Danny Wescott
 3. Emanuel Alanis
 4. Karen Lewis
 5. Carolyn Chang
 6. Lucia Summers
 7. Maria Resendiz
 8. Jelena Tesic
 9. Gregory Lakomski
10. Chiu Au
11. Ivan Ojeda-Ruiz
12. Young Ju Lee
13. Chul-Ho Lee
14. Keshav Bhandari
15. Vangelis Metsis
16. Mylene Farias
17. Ziliang Zong
18. Apan Qasem
19. Hyunhwan Kim
20. Jie Zhu
21. Yihong Yuan
22. Barbara Hewitt
23. Eunsang Cho
24. Feng Wang
25. Togay Ozbakkaloglu
26. Semih Aslan
27. Damian Valles
28. Wenquan Dong
29. Tongdan Jin
30. Nadim Adi
31. Francis Mendez
32. Tahir Ekin
33. Rasim Musal
34. Dincer Konur
35. Emily Zhu
36. Xiaoxi Shen
37. Monica Hughes
38. Holly Lewis
39. Denise Gobert
40. Shannon Williams
41. Subasish Das
42. Sean Bauld
43. Eduardo Perez
44. Ty Schepis
45. Larry Price
46. Erica Nason
47. Cindy Royal
48. David Gibbs
49. Diane Dolozel
50. Sarah Fritts
51. Edwin Chow
52. Li Feng
53. Vishan Shen
54. Holly Veselka
55. Toni Watt


## Files Generated:
1. `create_cads_tables.sql` - SQL script to create tables and migrate data
2. `cads_search_patterns.json` - Search patterns for name matching
3. `cads_migration_report.md` - This summary report

## Next Steps:
1. Run the SQL script in your Supabase SQL editor
2. Verify the data migration was successful
3. Use the cads_researcher_summary view to analyze the results

## Tables Created:
- `cads_researchers` - CADS faculty members
- `cads_works` - Publications by CADS faculty
- `cads_topics` - Research topics from CADS publications
- `cads_researcher_summary` - Summary view for analysis

## Expected Results:
The migration will identify and copy all researchers whose names match the CADS professor list,
along with all their publications and associated research topics.
